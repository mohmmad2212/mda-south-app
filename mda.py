import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title='מערכת מד"א דרום', layout='wide', page_icon='🚑')

# 2. ניהול קבצים (v10)
W_FILE, S_FILE, R_FILE = "workers_v10.csv", "shifts_v10.csv", "resets_v10.csv"
def load_db(file, cols): return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame(columns=cols)
def save_db(df, file): df.to_csv(file, index=False, encoding='utf-8-sig')

if 'workers_db' not in st.session_state: st.session_state.workers_db = load_db(W_FILE, ["שם", "תז", "סיסמה", "תפקיד", "טלפון"])
if 'shifts_db' not in st.session_state: st.session_state.shifts_db = load_db(S_FILE, ["תז", "שם_ותפקיד", "תחנה", "תאריך", "משמרת", "צבע", "סטטוס"])
if 'reset_db' not in st.session_state: st.session_state.reset_db = load_db(R_FILE, ["תז", "שם", "זמן", "סטטוס"])

# 3. הגדרות שעות וימי שבוע
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

# 4. עיצוב (כחול בחוץ, בהיר בפנים)
is_logged_in = 'auth' in st.session_state and st.session_state.auth is not None
bg_color = "#f4f7f9" if is_logged_in else "#1a3a6d"
text_color = "#1a3a6d" if is_logged_in else "#ffffff"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    .main-header {{ background-color: #ffffff; padding: 15px; border-radius: 15px; border-bottom: 6px solid #d32f2f; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .main-header h1 {{ color: #1a3a6d !important; margin: 0; }}
    label, .stMarkdown p, .stText {{ color: {text_color} !important; font-weight: bold; }}
    div[data-testid="stForm"] {{ background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #ddd; }}
    .stButton>button {{ background-color: #d32f2f !important; color: white !important; border-radius: 8px !important; width: 100%; }}
    .whatsapp-btn {{ background-color: #25D366 !important; color: white !important; padding: 10px; text-decoration: none; border-radius: 5px; display: block; text-align: center; font-weight: bold; margin-top: 5px; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🚑 מערכת שיבוץ - מד"א דרום</h1></div>', unsafe_allow_html=True)

# --- כניסה ---
if not is_logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        mode = st.radio("בחר סוג כניסה", ["עובד", "מנהל"], horizontal=True)
        with st.form("login"):
            uid, upw = st.text_input("תעודת זהות"), st.text_input("סיסמה", type="password")
            if st.form_submit_button("התחבר"):
                if mode == "מנהל" and upw == "123": st.session_state.auth = "admin"; st.rerun()
                else:
                    user = st.session_state.workers_db[st.session_state.workers_db['תז'].astype(str) == uid]
                    if not user.empty and str(user.iloc[0]['סיסמה']) == upw:
                        st.session_state.auth = "worker"; st.session_state.user = user.iloc[0]; st.rerun()
                    else: st.error("פרטים שגויים")

# --- ממשק מנהל ---
elif st.session_state.auth == "admin":
    st.sidebar.button("יציאה 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    tab1, tab2, tab3 = st.tabs(["👥 עובדים", "📥 בקשות", "📊 דוח וניהול"])

    with tab2: # אישור בקשות
        pending = st.session_state.shifts_db[st.session_state.shifts_db['סטטוס'] == "ממתין"]
        for idx, row in pending.iterrows():
            st.info(f"{row['שם_ותפקיד']} | {row['תחנה']} | {row['תאריך']}")
            c1, c2 = st.columns(2)
            if c1.button("אשר ✅", key=f"a{idx}"):
                st.session_state.shifts_db.at[idx, 'סטטוס'] = "מאושר ✅"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()
            if c2.button("דחה ❌", key=f"r{idx}"):
                st.session_state.shifts_db.at[idx, 'סטטוס'] = "מבוטל ❌"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()

    with tab3: # דוח + כפתור מחיקת הכל
        st.subheader("ניהול משמרות")
        if st.button("⚠️ איפוס מערכת - מחיקת כל המשמרות ⚠️"):
            st.session_state.shifts_db = pd.DataFrame(columns=st.session_state.shifts_db.columns)
            save_db(st.session_state.shifts_db, S_FILE); st.warning("כל המשמרות נמחקו!"); st.rerun()
        
        approved = st.session_state.shifts_db[st.session_state.shifts_db['סטטוס'] == "מאושר ✅"]
        st.dataframe(approved, use_container_width=True)

# --- ממשק עובד ---
else:
    st.sidebar.button("התנתק 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    u = st.session_state.user
    st.write(f"### שלום, {u['שם']}")
    
    # טופס הגשה
    br = st.selectbox("בחר תחנה", list(STATION_HOURS.keys()))
    with st.form("req"):
        sh, dt = st.radio("משמרת", STATION_HOURS[br]), st.selectbox("תאריך", get_week_days())
        if st.form_submit_button("שלח בקשה 🚑"):
            new_s = pd.DataFrame([[u['תז'], f"{u['שם']} ({u['תפקיד']})", br, dt, sh, "לבן", "ממתין"]], columns=st.session_state.shifts_db.columns)
            st.session_state.shifts_db = pd.concat([st.session_state.shifts_db, new_s], ignore_index=True)
            save_db(st.session_state.shifts_db, S_FILE); st.balloons(); st.rerun()

    # ניהול בקשות קיימות לעובד
    st.divider()
    st.subheader("הבקשות שלי")
    my_shifts = st.session_state.shifts_db[st.session_state.shifts_db['תז'].astype(str) == str(u['תז'])]
    for idx, row in my_shifts.iterrows():
        with st.expander(f"{row['תאריך']} - {row['תחנה']} ({row['סטטוס']})"):
            if row['סטטוס'] == "ממתין":
                c1, c2 = st.columns(2)
                if c1.button("מחק בקשה 🗑️", key=f"del_{idx}"):
                    st.session_state.shifts_db = st.session_state.shifts_db.drop(idx)
                    save_db(st.session_state.shifts_db, S_FILE); st.rerun()
                st.write("כדי לערוך, מחק את הבקשה והגש חדשה עם הפרטים הנכונים.")
            else:
                st.write("לא ניתן לשנות משמרת שכבר אושרה או בוטלה.")
