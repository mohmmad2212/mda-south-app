import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title='מערכת מד"א דרום', layout='wide', page_icon='🚑')

# 2. ניהול קבצים (v12)
W_FILE, S_FILE = "workers_v12.csv", "shifts_v12.csv"

def load_db(file, cols): 
    return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame(columns=cols)

def save_db(df, file): 
    df.to_csv(file, index=False, encoding='utf-8-sig')

# تحميل البيانات - العمال والورדיות بشكل منفصل تماماً
if 'workers_db' not in st.session_state: 
    st.session_state.workers_db = load_db(W_FILE, ["שם", "תז", "סיסמה", "תפקיד", "טלפון"])
if 'shifts_db' not in st.session_state: 
    st.session_state.shifts_db = load_db(S_FILE, ["תז", "שם_ותפקיד", "תחנה", "תאריך", "משמרת", "צבע", "סטטוס"])

# 3. הגדרות שעות
STATION_HOURS = {"חורה": ["07:00-15:00", "15:00-19:00"], "מיתר": ["07:00-15:00", "15:00-23:00"], "לקיה": ["08:00-16:00"]}

def get_week_days():
    days_names = {0: "שני", 1: "שלישי", 2: "רביעי", 3: "חמישי", 4: "שישי", 5: "שבת", 6: "ראשון"}
    today = datetime.now()
    start_point = today - timedelta(days=(today.weekday() + 1) % 7)
    return [f"{days_names[(start_point + timedelta(days=i)).weekday()]} - {(start_point + timedelta(days=i)).strftime('%d/%m/%Y')}" for i in range(7)]

# 4. עיצוב
is_logged_in = 'auth' in st.session_state and st.session_state.auth is not None
bg_color = "#f4f7f9" if is_logged_in else "#1a3a6d"
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    .main-header {{ background-color: #ffffff; padding: 15px; border-radius: 15px; border-bottom: 6px solid #d32f2f; text-align: center; margin-bottom: 25px; }}
    .main-header h1 {{ color: #1a3a6d !important; }}
    .reset-box {{ background-color: #ffcccc; padding: 20px; border-radius: 10px; border: 2px solid #d32f2f; margin-bottom: 20px; }}
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
    t1, t2, t3 = st.tabs(["👥 ניהול עובדים", "📥 בקשות חדשות", "📊 ניהול משמרות ואיפוס"])

    with t1: # ניהול עובדים - لا يتأثر بالتصفير
        st.subheader("רשימת עובדים קיימת")
        if not st.session_state.workers_db.empty:
            for idx, row in st.session_state.workers_db.iterrows():
                cols = st.columns([3, 2, 2, 1])
                cols[0].write(f"👤 **{row.get('שם', '')}**")
                cols[1].write(f"🆔 {row.get('תז', '')}")
                cols[2].write(f"🚑 {row.get('תפקיד', '')}")
                if cols[3].button("🗑️", key=f"del_w_{idx}"):
                    st.session_state.workers_db = st.session_state.workers_db.drop(idx)
                    save_db(st.session_state.workers_db, W_FILE); st.rerun()
        
        with st.expander("➕ הוספת עובד חדש למערכת"):
            with st.form("add_worker_form"):
                n, i, p, t = st.text_input("שם מלא"), st.text_input("תז"), st.text_input("סיסמה"), st.text_input("טלפון")
                r = st.selectbox("תפקיד", ["נוער חונך", "נוער חניך", "נוער", "חובש", "חובש (משתלם)", "משתלם נהיגה", "בת שירות"])
                if st.form_submit_button("שמור עובד"):
                    new_w = pd.DataFrame([[n, i, p, r, t]], columns=st.session_state.workers_db.columns)
                    st.session_state.workers_db = pd.concat([st.session_state.workers_db, new_w], ignore_index=True)
                    save_db(st.session_state.workers_db, W_FILE); st.success("העובד נוסף בהצלחה!"); st.rerun()

    with t3: # تصفير الورדיات فقط
        st.markdown('<div class="reset-box">', unsafe_allow_html=True)
        st.subheader("⚠️ איפוס משמרות (העובדים יישארו)")
        if st.button("🚨 מחק את כל המשמרות והתחל שבוע חדש 🚨"):
            # نقوم بتفريغ جدول الورדיات فقط
            st.session_state.shifts_db = pd.DataFrame(columns=["תז", "שם_ותפקיד", "תחנה", "תאריך", "משמרת", "צבע", "סטטוס"])
            save_db(st.session_state.shifts_db, S_FILE)
            st.success("המשמרות נמחקו. רשימת העובדים נשמרה בבטחה ✅")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.dataframe(st.session_state.shifts_db, use_container_width=True)

    with t2: # إدارة الطلبات
        pending = st.session_state.shifts_db[st.session_state.shifts_db['סטטוס'] == "ממתין"]
        if pending.empty: st.write("אין בקשות חדשות.")
        for idx, row in pending.iterrows():
            st.info(f"{row['שם_ותפקיד']} | {row['תחנה']} | {row['תאריך']} | {row['משמרת']}")
            c1, c2 = st.columns(2)
            if c1.button("אשר ✅", key=f"a{idx}"):
                st.session_state.shifts_db.at[idx, 'סטטוס'] = "מאושר ✅"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()
            if c2.button("דחה ❌", key=f"r{idx}"):
                st.session_state.shifts_db.at[idx, 'סטטוס'] = "מבוטל ❌"; save_db(st.session_state.shifts_db, S_FILE); st.rerun()

# --- ממשק עובד ---
else:
    st.sidebar.button("התנתק 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    u = st.session_state.user
    st.write(f"### שלום, {u['שם']}")
    br = st.selectbox("בחר תחנה", list(STATION_HOURS.keys()))
    with st.form("req"):
        sh, dt = st.radio("משמרת", STATION_HOURS[br]), st.selectbox("תאריך", get_week_days())
        if st.form_submit_button("שלח בקשה 🚑"):
            new_s = pd.DataFrame([[u['תז'], f"{u['שם']} ({u['תפקיד']})", br, dt, sh, "לבן", "ממתין"]], columns=st.session_state.shifts_db.columns)
            st.session_state.shifts_db = pd.concat([st.session_state.shifts_db, new_s], ignore_index=True)
            save_db(st.session_state.shifts_db, S_FILE); st.balloons(); st.rerun()

    st.divider()
    st.subheader("הבקשות שלי")
    my_shifts = st.session_state.shifts_db[st.session_state.shifts_db['תז'].astype(str) == str(u['תז'])]
    for idx, row in my_shifts.iterrows():
        col_text, col_del = st.columns([4, 1])
        col_text.write(f"📍 {row['תחנה']} | 📅 {row['תאריך']} | 🕒 {row['משמרת']} | 📝 {row['סטטוס']}")
        if row['סטטוס'] == "ממתין" and col_del.button("🗑️ מחק", key=f"del_s_{idx}"):
            st.session_state.shifts_db = st.session_state.shifts_db.drop(idx)
            save_db(st.session_state.shifts_db, S_FILE); st.rerun()
