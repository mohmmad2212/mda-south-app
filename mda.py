import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from PIL import Image

# 1. הגדרות דף
st.set_page_config(page_title='מערכת שיבוץ אשכול', layout='wide', page_icon='🚑')

# 2. ניהול קבצים
W_FILE, S_FILE = "workers_v27.csv", "shifts_v27.csv"
PIC_DIR = "profile_pics"
if not os.path.exists(PIC_DIR): os.makedirs(PIC_DIR)

def load_db(file, cols): return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame(columns=cols)
def save_db(df, file): df.to_csv(file, index=False, encoding='utf-8-sig')

if 'workers_db' not in st.session_state: 
    st.session_state.workers_db = load_db(W_FILE, ["שם", "תז", "סיסמה", "תפקיד", "טלפון", "תמונה"])
if 'shifts_db' not in st.session_state: 
    st.session_state.shifts_db = load_db(S_FILE, ["תז", "שם", "טלפון", "תחנה", "תאריך", "משמרת", "תפקיד", "צבע", "סטטוס"])

# 3. ניהול מנהלים (1 ראשי + 4 משניים)
# غير الأسماء والباسوردات هنا فقط
ADMIN_SUPER = {"اسم_اخوك": "123"} 
ADMIN_NORMAL = {
    "مدיר1": "111", 
    "مدיר2": "222", 
    "مدיר3": "333", 
    "مدיר4": "444"
}

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
bg_c = "#f4f7f9" if is_logged_in else "#1a3a6d"
txt_c = "#000000" if is_logged_in else "#ffffff"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_c}; }}
    .stMarkdown p, label, .stRadio label {{ color: {txt_c} !important; font-weight: bold !important; }}
    .main-header {{ background-color: #000000; padding: 20px; border-radius: 15px; border-bottom: 6px solid #d32f2f; text-align: center; margin-bottom: 20px; }}
    .main-header h1 {{ color: #ffffff !important; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🚑 מערכת שיבוץ אשכול חורה מיתר לקיה</h1></div>', unsafe_allow_html=True)

# --- כניסה ---
if not is_logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mode = st.radio("בחר סוג כניסה:", ["עובד", "מנהל"], horizontal=True)
        with st.form("login"):
            u_in = st.text_input("שם / תז")
            p_in = st.text_input("סיסמה", type="password")
            if st.form_submit_button("התחבר"):
                if mode == "מנהל":
                    if u_in in ADMIN_SUPER and ADMIN_SUPER[u_in] == p_in:
                        st.session_state.auth = "admin_super"; st.session_state.admin_name = u_in; st.rerun()
                    elif u_in in ADMIN_NORMAL and ADMIN_NORMAL[u_in] == p_in:
                        st.session_state.auth = "admin_normal"; st.session_state.admin_name = u_in; st.rerun()
                    else: st.error("פרטי מנהל שגויים")
                else:
                    u_db = st.session_state.workers_db
                    user_idx = u_db.index[u_db['תז'].astype(str) == u_in].tolist()
                    if user_idx and str(u_db.at[user_idx[0], 'סיסמה']) == p_in:
                        st.session_state.auth = "worker"; st.session_state.user_idx = user_idx[0]; st.rerun()
                    else: st.error("פרטי עובד שגויים")

# --- ממשק מנהל ---
elif st.session_state.auth.startswith("admin"):
    is_super = st.session_state.auth == "admin_super"
    st.sidebar.subheader(f"שלום, {st.session_state.admin_name}")
    st.sidebar.write("סוג מנהל: " + ("ראשי ⭐" if is_super else "רגيل"))
    st.sidebar.button("יציאה 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    
    t_names = ["📥 בקשות משמרת"]
    if is_super: t_names = ["👥 ניהול עובדים"] + t_names + ["📊 יומן ואיפוס"]
    
    tabs = st.tabs(t_names)

    if is_super:
        with tabs[0]: # ניהול עובדים
            with st.form("add"):
                n, i, p, t = st.text_input("שם"), st.text_input("תז"), st.text_input("סיסמה"), st.text_input("טלפון")
                r = st.selectbox("תפקיד", list(ROLES_CONFIG.keys()))
                if st.form_submit_button("הוסף עובד"):
                    nw = pd.DataFrame([[n, i, p, r, t, ""]], columns=st.session_state.workers_db.columns)
                    st.session_state.workers_db = pd.concat([st.session_state.workers_db, nw], ignore_index=True)
                    save_db(st.session_state.workers_db, W_FILE); st.rerun()
            for idx, row in st.session_state.workers_db.iterrows():
                c1, c2, c3 = st.columns([1, 4, 1])
                c1.write("👤")
                c2.write(f"**{row['שם']}** | {row['תפקיד']}")
                if c3.button("🗑️", key=f"d_{idx}"):
                    st.session_state.workers_db = st.session_state.workers_db.drop(idx); save_db(st.session_state.workers_db, W_FILE); st.rerun()

    with tabs[1 if is_super else 0]: # בקשות (לכולם)
        pending = st.session_state.shifts_db[st.session_state.shifts_db['סטטוס'] == "ממתין"]
        if pending.empty: st.info("אין בקשות ממתינות")
        for idx, row in pending.iterrows():
            with st.expander(f"בקשה מ-{row['שם']} ({row['תחנה']})"):
                st.write(f"📅 {row['תאריך']} | 🕒 {row['משמרת']}")
                ca, cr = st.columns(2)
                if ca.button("✅ אשרי", key=f"ok_{idx}"):
                    st.session_state.shifts_db.at[idx, 'סטטוס'] = "מאושר ✅"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()
                if cr.button("❌ דחה", key=f"no_{idx}"):
                    st.session_state.shifts_db.at[idx, 'סטטוס'] = "מבוטל ❌"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()

    if is_super:
        with tabs[2]: # אקסל ואיפוס
            approved = st.session_state.shifts_db[st.session_state.shifts_db['סטטוס'] == "מאושר ✅"]
            st.dataframe(approved[["תאריך", "שם", "תחנה", "משמרת"]])
            if not approved.empty:
                csv = approved.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("📥 הורד לאקסל", csv, "report.csv", "text/csv")
            st.divider()
            if st.button("🚨 איפוס מערכת"): st.session_state.confirm = True
            if st.session_state.get('confirm'):
                if st.button("אישור סופי למחיקה"):
                    st.session_state.shifts_db = pd.DataFrame(columns=st.session_state.shifts_db.columns)
                    save_db(st.session_state.shifts_db, S_FILE); st.session_state.confirm = False; st.rerun()

# --- ממשק עובד ---
else:
    st.sidebar.button("התנתק 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    u_idx = st.session_state.user_idx
    u = st.session_state.workers_db.iloc[u_idx]
    if pd.isna(u['תמונה']) or u['תמונה'] == "" or not os.path.exists(u['תמונה']):
        st.warning("נא להעלות תמונה")
        up = st.file_uploader("בחר תמונה", type=['jpg', 'png'])
        if up:
            img = Image.open(up); path = os.path.join(PIC_DIR, f"{u['תז']}.png"); img.save(path)
            st.session_state.workers_db.at[u_idx, 'תמונה'] = path; save_db(st.session_state.workers_db, W_FILE); st.rerun()
    else:
        st.write(f"### שלום, {u['שם']}! 👋")
        st.image(u['תמונה'], width=100)
        st_branch = st.selectbox("בחר תחנה", list(STATION_HOURS.keys()))
        with st.form("req"):
            s_time, s_date = st.radio("משמרת", STATION_HOURS[st_branch]), st.selectbox("תאריך", get_week_days())
            if st.form_submit_button("שלח בקשה 🚑"):
                new_row = pd.DataFrame([[u['תז'], u['שם'], u['טלפון'], st_branch, s_date, s_time, u['תפקיד'], ROLES_CONFIG.get(u['תפקיד'], "#FFF"), "ממתין"]], columns=st.session_state.shifts_db.columns)
                st.session_state.shifts_db = pd.concat([st.session_state.shifts_db, new_row], ignore_index=True)
                save_db(st.session_state.shifts_db, S_FILE); st.balloons(); st.rerun()
