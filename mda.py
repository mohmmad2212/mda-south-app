import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. הגדרות דף
st.set_page_config(page_title='מערכת שיבוץ אשכול', layout='wide', page_icon='🚑')

# 2. ניהול קבצים
W_FILE, S_FILE = "workers_v17.csv", "shifts_v17.csv"
def load_db(file, cols): return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame(columns=cols)
def save_db(df, file): df.to_csv(file, index=False, encoding='utf-8-sig')

if 'workers_db' not in st.session_state: st.session_state.workers_db = load_db(W_FILE, ["שם", "תז", "סיסמה", "תפקיד", "טלפון"])
if 'shifts_db' not in st.session_state: st.session_state.shifts_db = load_db(S_FILE, ["תז", "שם_ותפקיד", "תחנה", "תאריך", "משמרת", "צבע", "סטטוס"])

# 3. רשימת התפקידים החדשה (לפי התמונה שלך)
ROLES_CONFIG = {
    "נוער חונך": "#9370DB",       # סגול
    "נוער חניך": "#FA8072",       # סלמון/אדום בהיר
    "נוער": "#FF0000",             # אדום
    "חובש": "#808080",             # אפור
    "חובש (משתלם)": "#D3D3D3",    # אפור בהיר
    "משתלם נהיגה": "#FFD700",      # צהוב
    "בת שירות": "#87CEEB"         # כחול בהיר
}

# 4. הגדרות שעות ותחנות
STATION_HOURS = {"חורה": ["07:00-15:00", "15:00-19:00"], "מיתר": ["07:00-15:00", "15:00-23:00"], "לקיה": ["08:00-16:00"]}

def get_week_days():
    days_names = {0: "שני", 1: "שלישי", 2: "רביעי", 3: "חמישי", 4: "שישי", 5: "שבת", 6: "ראשון"}
    today = datetime.now()
    start_point = today - timedelta(days=(today.weekday() + 1) % 7)
    return [f"{days_names[(start_point + timedelta(days=i)).weekday()]} - {(start_point + timedelta(days=i)).strftime('%d/%m/%Y')}" for i in range(7)]

# 5. עיצוב (צבעים שחור ולבן לפי בקשתך)
is_logged_in = 'auth' in st.session_state and st.session_state.auth is not None
bg_color = "#f4f7f9" if is_logged_in else "#1a3a6d"
label_color = "#000000" if is_logged_in else "#ffffff" # שחור כשהוא מחובר

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
    .stButton>button {{ background-color: #d32f2f !important; color: white !important; font-weight: bold; border-radius: 10px; }}
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
            if st.form_submit_button("התחבר למערכת"):
                if mode == "מנהל" and upw == "123":
                    st.session_state.auth = "admin"; st.rerun()
                else:
                    user = st.session_state.workers_db[st.session_state.workers_db['תז'].astype(str) == uid]
                    if not user.empty and str(user.iloc[0]['סיסמה']) == upw:
                        st.session_state.auth = "worker"; st.session_state.user = user.iloc[0]
                        st.toast(f"ברוך הבא, {user.iloc[0]['שם']}! 👋")
                        st.rerun()
                    else: st.error("פרטים שגויים")

# --- ממשק מנהל ---
elif st.session_state.auth == "admin":
    st.sidebar.button("יציאה 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    t1, t2, t3 = st.tabs(["👥 ניהול עובדים", "📥 בקשות משמרת", "📊 דוח משמרות"])

    with t1:
        st.subheader("הוספת עובד חדש")
        with st.form("add_worker"):
            n, i, p = st.text_input("שם מלא"), st.text_input("תז"), st.text_input("סיסמה")
            r = st.selectbox("תפקיד (מהרשימה המעודכנת)", list(ROLES_CONFIG.keys()))
            if st.form_submit_button("שמור עובד ✅"):
                nw = pd.DataFrame([[n, i, p, r, ""]], columns=st.session_state.workers_db.columns)
                st.session_state.workers_db = pd.concat([st.session_state.workers_db, nw], ignore_index=True)
                save_db(st.session_state.workers_db, W_FILE); st.success(f"העובד {n} נוסף!"); st.rerun()
        
        st.divider()
        st.subheader("רשימת עובדים קיימת")
        for idx, row in st.session_state.workers_db.iterrows():
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(f"👤 {row['שם']} - **{row['תפקיד']}**")
            if c3.button("🗑️", key=f"delw_{idx}"):
                st.session_state.workers_db = st.session_state.workers_db.drop(idx)
                save_db(st.session_state.workers_db, W_FILE); st.rerun()

    with t2:
        pending = st.session_state.shifts_db[st.session_state.shifts_db['סטטוס'] == "ממתין"]
        if pending.empty: st.info("אין בקשות חדשות")
        for idx, row in pending.iterrows():
            st.warning(f"🔔 {row['שם_ותפקיד']} | {row['תחנה']} | {row['תאריך']} | {row['משמרת']}")
            ca, cr = st.columns(2)
            if ca.button("✅ אשרי משמרת", key=f"app_{idx}"):
                st.session_state.shifts_db.at[idx, 'סטטוס'] = "מאושר ✅"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()
            if cr.button("❌ דחה בקשה", key=f"rej_{idx}"):
                st.session_state.shifts_db.at[idx, 'סטטוס'] = "מבוטל ❌"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()

# --- ממשק עובד ---
else:
    st.sidebar.button("התנתק 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    u = st.session_state.user
    st.write(f"### שלום, {u['שם']}! 👋")
    
    with st.form("shift_request"):
        st.write("### שליחת בקשה למשמרת")
        station = st.selectbox("בחר תחנה", list(STATION_HOURS.keys()))
        day = st.selectbox("בחר תאריך", get_week_days())
        shift_time = st.radio("בחר משמרת", STATION_HOURS[station])
        
        if st.form_submit_button("שלח בקשה 🚑"):
            # צבע המשמרת נקבע לפי התפקיד של העובד
            shift_color = ROLES_CONFIG.get(u['תפקיד'], "#FFFFFF")
            new_req = pd.DataFrame([[u['תז'], f"{u['שם']} ({u['תפקיد']})", station, day, shift_time, shift_color, "ממתין"]], 
                                   columns=st.session_state.shifts_db.columns)
            st.session_state.shifts_db = pd.concat([st.session_state.shifts_db, new_req], ignore_index=True)
            save_db(st.session_state.shifts_db, S_FILE)
            st.balloons()
            st.success("תודה על שליחת המשמרת! 🙏 נא להמתין בסבלנות עד לאישור המנהל.")
            st.rerun()

    st.divider()
    st.subheader("📋 הבקשות שלי")
    my_s = st.session_state.shifts_db[st.session_state.shifts_db['תז'].astype(str) == str(u['תז'])]
    for idx, row in my_s.iterrows():
        ci, cs, ca = st.columns([3, 1, 1])
        ci.write(f"📍 {row['תחנה']} | 📅 {row['תאריך']} | 🕒 {row['משמרת']}")
        cs.write(f"**{row['סטטוס']}**")
        if row['סטטוס'] == "ממתין" and ca.button("🗑️ מחק", key=f"del_s_{idx}"):
            st.session_state.shifts_db = st.session_state.shifts_db.drop(idx)
            save_db(st.session_state.shifts_db, S_FILE); st.rerun()
