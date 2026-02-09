import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# 1. הגדרות דף
st.set_page_config(page_title='מערכת שיבוץ אשכול', layout='wide', page_icon='🚑')

# 2. ניהול קבצים
W_FILE, S_FILE = "workers_v16.csv", "shifts_v16.csv"
def load_db(file, cols): return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame(columns=cols)
def save_db(df, file): df.to_csv(file, index=False, encoding='utf-8-sig')

if 'workers_db' not in st.session_state: st.session_state.workers_db = load_db(W_FILE, ["שם", "תז", "סיסמה", "תפקיד", "טלפון"])
if 'shifts_db' not in st.session_state: st.session_state.shifts_db = load_db(S_FILE, ["תז", "שם_ותפקיד", "תחנה", "תאריך", "משמרת", "צבע", "סטטוס"])

# 3. הגדרות שעות
STATION_HOURS = {"חורה": ["07:00-15:00", "15:00-19:00"], "מיתר": ["07:00-15:00", "15:00-23:00"], "לקיה": ["08:00-16:00"]}

def get_week_days():
    days_names = {0: "שני", 1: "שלישי", 2: "רביעי", 3: "חמישי", 4: "שישי", 5: "שבת", 6: "ראשון"}
    today = datetime.now()
    start_point = today - timedelta(days=(today.weekday() + 1) % 7)
    return [f"{days_names[(start_point + timedelta(days=i)).weekday()]} - {(start_point + timedelta(days=i)).strftime('%d/%m/%Y')}" for i in range(7)]

# 4. עיצוב מעודכן
is_logged_in = 'auth' in st.session_state and st.session_state.auth is not None
bg_color = "#f4f7f9" if is_logged_in else "#1a3a6d"
# تعديل اللون هنا ليكون أسود للكلمات تحت الصندوق
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
                        st.toast(f"ברוך הבא, {user.iloc[0]['שם']}! 👋") # رسالة ترحيب منبثقة
                        st.rerun()
                    else: st.error("פרטים שגויים")

# --- ממשק מנהל ---
elif st.session_state.auth == "admin":
    st.sidebar.button("יציאה 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    st.write("### שלום, מנהל המערכת")
    t1, t2, t3 = st.tabs(["👥 ניהול עובדים", "📥 בקשות", "📊 איפוס ודוחות"])
    # (الأكواد المعتادة للمدير تظل كما هي في النسخ السابقة...)
    with t3:
        if st.button("🚨 למחוק את כל המשמרות"):
            st.session_state.shifts_db = pd.DataFrame(columns=st.session_state.shifts_db.columns)
            save_db(st.session_state.shifts_db, S_FILE); st.rerun()
        st.dataframe(st.session_state.shifts_db)
    with t1:
        with st.expander("➕ הוסף עובד"):
            with st.form("add_w"):
                n, i, p = st.text_input("שם"), st.text_input("תז"), st.text_input("סיסמה")
                r = st.selectbox("תפקיד", ["נוער", "חובש", "נהג"])
                if st.form_submit_button("שמור"):
                    nw = pd.DataFrame([[n, i, p, r, ""]], columns=st.session_state.workers_db.columns)
                    st.session_state.workers_db = pd.concat([st.session_state.workers_db, nw], ignore_index=True)
                    save_db(st.session_state.workers_db, W_FILE); st.rerun()
    with t2:
        pending = st.session_state.shifts_db[st.session_state.shifts_db['סטטוס'] == "ממתין"]
        for idx, row in pending.iterrows():
            st.info(f"{row['שם_ותפקיד']} | {row['תחנה']}")
            if st.button("✅ אשרי", key=f"a{idx}"):
                st.session_state.shifts_db.at[idx, 'סטטוס'] = "מאושר ✅"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()

# --- ממשק עובד ---
else:
    st.sidebar.button("התנתק 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    u = st.session_state.user
    
    # 1. رسالة ترحيب واضحة
    st.markdown(f"### שלום, {u['שם']}! שמחים לראות אותך 👋")
    
    br = st.selectbox("בחר תחנה", list(STATION_HOURS.keys()))
    with st.form("req"):
        sh, dt = st.radio("משמרת", STATION_HOURS[br]), st.selectbox("תאריך", get_week_days())
        if st.form_submit_button("שלח בקשה 🚑"):
            new_s = pd.DataFrame([[u['תז'], f"{u['שם']} ({u['תפקיد']})", br, dt, sh, "לבן", "ממתין"]], columns=st.session_state.shifts_db.columns)
            st.session_state.shifts_db = pd.concat([st.session_state.shifts_db, new_s], ignore_index=True)
            save_db(st.session_state.shifts_db, S_FILE)
            
            # 2. تأثير البلالين ورسالة الشكر
            st.balloons()
            st.success("תודה על שליחת המשמרת! 🙏 נא להמתין בסבלנות עד לאישור המנהל.")
            st.rerun()

    st.divider()
    st.subheader("📋 ניהול המשמרות שלי")
    my_shifts = st.session_state.shifts_db[st.session_state.shifts_db['תז'].astype(str) == str(u['תז'])]
    for idx, row in my_shifts.iterrows():
        c_i, c_s, c_a = st.columns([3, 1, 1])
        c_i.write(f"📍 {row['תחנה']} | 📅 {row['תאריך']} | 🕒 {row['משמרת']}")
        c_s.write(f"**סטטוס:** {row['סטטוס']}")
        if row['סטטוס'] == "ממתין" and c_a.button("🗑️ מחק", key=f"ds_{idx}"):
            st.session_state.shifts_db = st.session_state.shifts_db.drop(idx)
            save_db(st.session_state.shifts_db, S_FILE); st.rerun()
