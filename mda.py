import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from PIL import Image

# 1. הגדרות דף
st.set_page_config(page_title='מערכת שיבוץ אשכול', layout='wide', page_icon='🚑')

# 2. ניהול קבצים ותיקיות
W_FILE, S_FILE = "workers_v24.csv", "shifts_v24.csv"
PIC_DIR = "profile_pics"
if not os.path.exists(PIC_DIR): os.makedirs(PIC_DIR)

def load_db(file, cols): return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame(columns=cols)
def save_db(df, file): df.to_csv(file, index=False, encoding='utf-8-sig')

if 'workers_db' not in st.session_state: 
    st.session_state.workers_db = load_db(W_FILE, ["שם", "תז", "סיסמה", "תפקיד", "טלפון", "תמונה"])
if 'shifts_db' not in st.session_state: 
    st.session_state.shifts_db = load_db(S_FILE, ["תז", "שם", "טלפון", "תחנה", "תאריך", "משמרת", "תפקיד", "צבע", "סטטוס"])

# 3. רשימת תפקידים
ROLES_CONFIG = {
    "נוער חונך": "#9370DB", "נוער חניך": "#FA8072", "נוער": "#FF0000",
    "חובש": "#808080", "חובש (משתלם)": "#D3D3D3", "משתלם נהיגה": "#FFD700", "בת שירות": "#87CEEB"
}

STATION_HOURS = {
    "חורה": ["07:00-15:00", "15:00-19:00"],
    "מיתר": ["07:00-15:00", "15:00-23:00"],
    "לקיה": ["08:00-16:00"]
}

def get_week_days():
    days_names = {0: "שני", 1: "שלישי", 2: "רביעי", 3: "חמישי", 4: "שישי", 5: "שבת", 6: "ראשון"}
    today = datetime.now()
    start_point = today - timedelta(days=(today.weekday() + 1) % 7)
    return [f"{days_names[(start_point + timedelta(days=i)).weekday()]} - {(start_point + timedelta(days=i)).strftime('%d/%m/%Y')}" for i in range(7)]

# 4. עיצוב CSS
is_logged_in = 'auth' in st.session_state and st.session_state.auth is not None
label_color = "#000000" if is_logged_in else "#ffffff"

st.markdown(f"""
    <style>
    .stApp {{ background-color: { "#f4f7f9" if is_logged_in else "#1a3a6d"}; }}
    .stMarkdown p, label, .stRadio label {{ color: {label_color} !important; font-weight: bold !important; }}
    .main-header {{ 
        background-color: #000000; padding: 20px; border-radius: 15px; border-bottom: 6px solid #d32f2f; 
        text-align: center; margin-bottom: 25px; }}
    .main-header h1 {{ color: #ffffff !important; }}
    .profile-img {{ border-radius: 50%; border: 3px solid #d32f2f; object-fit: cover; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🚑 מערכת שיבוץ אשכול חורה מיתר לקיה</h1></div>', unsafe_allow_html=True)

# --- דף כניסה ---
if not is_logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mode = st.radio("בחר סוג כניסה:", ["עובד", "מנהל"], horizontal=True)
        with st.form("login"):
            uid, upw = st.text_input("תעודת זהות"), st.text_input("סיסמה", type="password")
            if st.form_submit_button("התחבר"):
                if mode == "מנהל" and upw == "123": st.session_state.auth = "admin"; st.rerun()
                else:
                    user_idx = st.session_state.workers_db.index[st.session_state.workers_db['תז'].astype(str) == uid].tolist()
                    if user_idx and str(st.session_state.workers_db.at[user_idx[0], 'סיסמה']) == upw:
                        st.session_state.auth = "worker"; st.session_state.user_idx = user_idx[0]; st.rerun()
                    else: st.error("פרטים שגויים")

# --- ממשק מנהל ---
elif st.session_state.auth == "admin":
    st.sidebar.button("יציאה 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    t1, t2, t3 = st.tabs(["👥 ניהול עובדים", "📥 בקשות", "📊 יומן ואיפוס"])

    with t1:
        with st.form("add"):
            n, i, p, t = st.text_input("שם"), st.text_input("תז"), st.text_input("סיסמה"), st.text_input("טלפון")
            r = st.selectbox("תפקיד", list(ROLES_CONFIG.keys()))
            if st.form_submit_button("הוסף עובד"):
                nw = pd.DataFrame([[n, i, p, r, t, ""]], columns=st.session_state.workers_db.columns)
                st.session_state.workers_db = pd.concat([st.session_state.workers_db, nw], ignore_index=True)
                save_db(st.session_state.workers_db, W_FILE); st.rerun()
        
        for idx, row in st.session_state.workers_db.iterrows():
            c1, c2, c3 = st.columns([1, 4, 1])
            img_path = row['תמונה'] if pd.notna(row['תמונה']) and row['תמונה'] != "" else None
            if img_path and os.path.exists(img_path): c1.image(img_path, width=50)
            else: c1.write("👤")
            c2.write(f"**{row['שם']}** ({row['תפקיד']})")
            if c3.button("🗑️", key=f"dw_{idx}"):
                st.session_state.workers_db = st.session_state.workers_db.drop(idx); save_db(st.session_state.workers_db, W_FILE); st.rerun()

    with t2:
        pending = st.session_state.shifts_db[st.session_state.shifts_db['סטטוס'] == "ממתין"]
        for idx, row in pending.iterrows():
            # جلب صورة العامل من قاعدة بيانات العمال
            worker_data = st.session_state.workers_db[st.session_state.workers_db['תז'].astype(str) == str(row['תז'])]
            with st.expander(f"בקשה מ-{row['שם']}"):
                col_img, col_txt = st.columns([1, 4])
                if not worker_data.empty and pd.notna(worker_data.iloc[0]['תמונה']) and os.path.exists(worker_data.iloc[0]['תמונה']):
                    col_img.image(worker_data.iloc[0]['תמונה'], width=100)
                col_txt.write(f"📍 {row['תחנה']} | 📅 {row['תאריך']} | 🕒 {row['משמרת']}")
                ca, cr = st.columns(2)
                if ca.button("✅ אשרי", key=f"ok_{idx}"):
                    st.session_state.shifts_db.at[idx, 'סטטוס'] = "מאושר ✅"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()
                if cr.button("❌ דחה", key=f"no_{idx}"):
                    st.session_state.shifts_db.at[idx, 'סטטוס'] = "מבוטל ❌"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()

# --- ממשק עובד ---
else:
    st.sidebar.button("התנתק 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    u_idx = st.session_state.user_idx
    u = st.session_state.workers_db.iloc[u_idx]
    
    col_u1, col_u2 = st.columns([1, 5])
    # التحقق من الصورة
    if pd.isna(u['תמונה']) or u['תמונה'] == "" or not os.path.exists(u['תמונה']):
        with col_u2:
            st.warning("נא להעלות תמונת פרופיל כדי להמשיך")
            uploaded_file = st.file_uploader("בחר תמונה", type=['jpg', 'png', 'jpeg'])
            if uploaded_file:
                img = Image.open(uploaded_file)
                path = os.path.join(PIC_DIR, f"{u['תז']}.png")
                img.save(path)
                st.session_state.workers_db.at[u_idx, 'תמונה'] = path
                save_db(st.session_state.workers_db, W_FILE)
                st.success("התמונה נשמרה!")
                st.rerun()
    else:
        col_u1.image(u['תמונה'], width=100)
        col_u2.write(f"### שלום, {u['שם']}! 👋")
        
        # نموذج الطلب (لا يظهر إلا بعد رفع الصورة)
        st_branch = st.selectbox("בחר תחנה", list(STATION_HOURS.keys()))
        with st.form("req"):
            s_time, s_date = st.radio("משמרת", STATION_HOURS[st_branch]), st.selectbox("תאריך", get_week_days())
            if st.form_submit_button("שלח בקשה 🚑"):
                new_row = pd.DataFrame([[u['תז'], u['שם'], u['טלפון'], st_branch, s_date, s_time, u['תפקיד'], ROLES_CONFIG.get(u['תפקיד'], "#FFF"), "ממתין"]], 
                                       columns=st.session_state.shifts_db.columns)
                st.session_state.shifts_db = pd.concat([st.session_state.shifts_db, new_row], ignore_index=True)
                save_db(st.session_state.shifts_db, S_FILE); st.balloons(); st.rerun()
