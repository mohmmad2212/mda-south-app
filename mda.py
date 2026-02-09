import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. הגדרות דף
st.set_page_config(page_title='מערכת שיבוץ אשכול', layout='wide', page_icon='🚑')

# 2. ניהול קבצים
W_FILE, S_FILE = "workers_v23.csv", "shifts_v23.csv"
def load_db(file, cols): return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame(columns=cols)
def save_db(df, file): df.to_csv(file, index=False, encoding='utf-8-sig')

if 'workers_db' not in st.session_state: 
    st.session_state.workers_db = load_db(W_FILE, ["שם", "תז", "סיסמה", "תפקיד", "טלפון"])
if 'shifts_db' not in st.session_state: 
    st.session_state.shifts_db = load_db(S_FILE, ["תז", "שם", "טלפון", "תחנה", "תאריך", "משמרת", "תפקיד", "צבע", "סטטוס"])

# 3. רשימת תפקידים (מהתמונה שלך)
ROLES_CONFIG = {
    "נוער חונך": "#9370DB", "נוער חניך": "#FA8072", "נוער": "#FF0000",
    "חובש": "#808080", "חובש (משתלם)": "#D3D3D3", "משתלם נהיגה": "#FFD700", "בת שירות": "#87CEEB"
}

# 4. שעות פעילות לכל תחנה
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

# 5. עיצוב CSS
is_logged_in = 'auth' in st.session_state and st.session_state.auth is not None
bg_color = "#f4f7f9" if is_logged_in else "#1a3a6d"
label_color = "#000000" if is_logged_in else "#ffffff"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    .stMarkdown p, label, .stRadio label {{ color: {label_color} !important; font-weight: bold !important; }}
    .main-header {{ 
        background-color: #000000; padding: 20px; border-radius: 15px; border-bottom: 6px solid #d32f2f; 
        text-align: center; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }}
    .main-header h1 {{ color: #ffffff !important; font-size: 1.8rem; margin: 0; }}
    div[data-testid="stForm"] {{ background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #ddd; }}
    .stButton>button {{ width: 100%; font-weight: bold; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🚑 מערכת שיבוץ אשכול חורה מיתר לקיה</h1></div>', unsafe_allow_html=True)

# --- דף כניסה ---
if not is_logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mode = st.radio("בחר סוג כניסה:", ["עובד", "מנהל"], horizontal=True)
        with st.form("login_form"):
            uid, upw = st.text_input("תעודת זהות"), st.text_input("סיסמה", type="password")
            if st.form_submit_button("התחבר"):
                if mode == "מנהל" and upw == "Meke3006": st.session_state.auth = "admin"; st.rerun()
                else:
                    user = st.session_state.workers_db[st.session_state.workers_db['תז'].astype(str) == uid]
                    if not user.empty and str(user.iloc[0]['סיסמה']) == upw:
                        st.session_state.auth = "worker"; st.session_state.user = user.iloc[0]; st.rerun()
                    else: st.error("פרטים שגויים")

# --- ממשק מנהל ---
elif st.session_state.auth == "admin":
    st.sidebar.button("יציאה 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    t1, t2, t3 = st.tabs(["👥 ניהול עובדים", "📥 בקשות ממתינות", "📊 יומן משמרות ואיפוס"])

    with t1:
        st.subheader("הוספת עובד חדש")
        with st.form("add_worker_form"):
            n, i, p, t = st.text_input("שם מלא"), st.text_input("תעודת זהות"), st.text_input("סיסמה"), st.text_input("טלפון")
            r = st.selectbox("תפקיד", list(ROLES_CONFIG.keys()))
            if st.form_submit_button("שמור עובד ✅"):
                nw = pd.DataFrame([[n, i, p, r, t]], columns=st.session_state.workers_db.columns)
                st.session_state.workers_db = pd.concat([st.session_state.workers_db, nw], ignore_index=True)
                save_db(st.session_state.workers_db, W_FILE); st.success(f"העובד {n} נוסף בהצלחה!"); st.rerun()
        
        st.divider()
        st.subheader("רשימת עובדים קיימת (מחיקה)")
        if st.session_state.workers_db.empty:
            st.info("אין עובדים רשומים במערכת.")
        else:
            for idx, row in st.session_state.workers_db.iterrows():
                cw1, cw2, cw3 = st.columns([3, 2, 1])
                cw1.write(f"👤 {row['שם']} ({row['תפקיד']})")
                cw2.write(f"🆔 {row['תז']}")
                if cw3.button("🗑️ מחק", key=f"del_worker_{idx}"):
                    st.session_state.workers_db = st.session_state.workers_db.drop(idx)
                    save_db(st.session_state.workers_db, W_FILE)
                    st.rerun()

    with t2:
        pending = st.session_state.shifts_db[st.session_state.shifts_db['סטטוס'] == "ממתין"]
        for idx, row in pending.iterrows():
            st.info(f"👤 {row['שם']} | 📍 {row['תחנה']} | 📅 {row['תאריך']}")
            c1, c2 = st.columns(2)
            if c1.button("✅ אשרי", key=f"ok_{idx}"):
                st.session_state.shifts_db.at[idx, 'סטטוס'] = "מאושר ✅"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()
            if c2.button("❌ דחה", key=f"no_{idx}"):
                st.session_state.shifts_db.at[idx, 'סטטוס'] = "מבוטל ❌"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()

    with t3:
        approved = st.session_state.shifts_db[st.session_state.shifts_db['סטטוס'] == "מאושר ✅"]
        st.dataframe(approved[["תאריך", "שם", "תז", "טלפון", "תחנה", "משמרת"]])
        if not approved.empty:
            csv = approved.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 הורד לאקסל (Excel)", csv, "report.csv", "text/csv")
        
        st.divider()
        if st.button("🚨 איפוס כל המשמרות"): st.session_state.confirm_reset = True
        
        if st.session_state.get('confirm_reset'):
            st.warning("האם אתה בטוח שברצונך למחוק את כל נתוני המשמרות?")
            col_y, col_n = st.columns(2)
            if col_y.button("כן, מחק הכל"):
                st.session_state.shifts_db = pd.DataFrame(columns=st.session_state.shifts_db.columns)
                save_db(st.session_state.shifts_db, S_FILE)
                st.session_state.confirm_reset = False; st.rerun()
            if col_n.button("ביטול"):
                st.session_state.confirm_reset = False; st.rerun()

# --- ממשק עובד ---
else:
    st.sidebar.button("התנתק 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    u = st.session_state.user
    st.write(f"### שלום, {u['שם']}! 👋")
    
    st_branch = st.selectbox("בחר תחנה", list(STATION_HOURS.keys()))
    with st.form("req"):
        s_time = st.radio("בחר משמרת", STATION_HOURS[st_branch])
        s_date = st.selectbox("בחר תאריך", get_week_days())
        if st.form_submit_button("שלח בקשה 🚑"):
            role_color = ROLES_CONFIG.get(u['תפקיד'], "#FFFFFF")
            new_row = pd.DataFrame([[u['תז'], u['שם'], u['טלפון'], st_branch, s_date, s_time, u['תפקיד'], role_color, "ממתין"]], 
                                columns=st.session_state.shifts_db.columns)
            st.session_state.shifts_db = pd.concat([st.session_state.shifts_db, new_row], ignore_index=True)
            save_db(st.session_state.shifts_db, S_FILE); st.balloons(); st.rerun()

    st.divider()
    my_s = st.session_state.shifts_db[st.session_state.shifts_db['תז'].astype(str) == str(u['תז'])]
    st.subheader("📋 הבקשות שלי")
    for idx, row in my_s.iterrows():
        c1, c2 = st.columns([4, 1])
        c1.write(f"📍 {row['תחנה']} | 📅 {row['תאריך']} | {row['משמרת']} | **{row['סטטוס']}**")
        if row['סטטוס'] == "ממתין" and c2.button("🗑️", key=f"del_{idx}"):
            st.session_state.shifts_db = st.session_state.shifts_db.drop(idx)
            save_db(st.session_state.shifts_db, S_FILE); st.rerun()
