import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import urllib.parse

# 1. הגדרות דף
st.set_page_config(page_title='מערכת מד"א דרום', layout='wide', page_icon='🚑')

# 2. ניהול קבצים (v9)
W_FILE, S_FILE, R_FILE = "workers_v9.csv", "shifts_v9.csv", "resets_v9.csv"
def load_db(file, cols): return pd.read_csv(file) if os.path.exists(file) else pd.DataFrame(columns=cols)
def save_db(df, file): df.to_csv(file, index=False, encoding='utf-8-sig')

if 'workers_db' not in st.session_state: st.session_state.workers_db = load_db(W_FILE, ["שם", "תז", "סיסמה", "תפקיד", "טלפון"])
if 'shifts_db' not in st.session_state: st.session_state.shifts_db = load_db(S_FILE, ["תז", "שם_ותפקיד", "תחנה", "תאריך", "משמרת", "צבע", "סטטוס"])
if 'reset_db' not in st.session_state: st.session_state.reset_db = load_db(R_FILE, ["תז", "שם", "זמן", "סטטוס"])

# 3. הגדרת שעות פעילות
STATION_HOURS = {
    "חורה": ["07:00-15:00", "15:00-19:00"],
    "מיתר": ["07:00-15:00", "15:00-23:00"],
    "לקיה": ["08:00-16:00"]
}

def get_week_days():
    days_names = {0: "שני", 1: "שלישי", 2: "רביעי", 3: "חמישי", 4: "שישי", 5: "שבת", 6: "ראשון"}
    today = datetime.now()
    start_point = today - timedelta(days=(today.weekday() + 1) % 7)
    week_list = []
    for i in range(7):
        current_day = start_point + timedelta(days=i)
        day_str = f"{days_names[current_day.weekday()]} - {current_day.strftime('%d/%m/%Y')}"
        week_list.append(day_str)
    return week_list

# 4. עיצוב דינמי
is_logged_in = 'auth' in st.session_state and st.session_state.auth is not None
bg_color = "#f4f7f9" if is_logged_in else "#1a3a6d"
text_color = "#1a3a6d" if is_logged_in else "#ffffff"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    .main-header {{
        background-color: #ffffff; padding: 15px; border-radius: 15px; border-bottom: 6px solid #d32f2f;
        text-align: center; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    .main-header h1 {{ color: #1a3a6d !important; margin: 0; }}
    label, .stMarkdown p, .stText {{ color: {text_color} !important; font-weight: bold; }}
    div[data-testid="stForm"] {{ background-color: #ffffff; padding: 25px; border-radius: 15px; border: 1px solid #ddd; }}
    .stButton>button {{ background-color: #d32f2f !important; color: white !important; border-radius: 8px !important; width: 100%; }}
    .whatsapp-btn {{ background-color: #25D366 !important; color: white !important; padding: 10px; text-decoration: none; border-radius: 5px; display: block; text-align: center; font-weight: bold; margin-top: 5px; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🚑 מערכת שיבוץ - מד"א דרום</h1></div>', unsafe_allow_html=True)

# --- דף כניסה ---
if not is_logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        mode = st.radio("בחר סוג כניסה", ["עובד", "מנהל"], horizontal=True)
        with st.form("login"):
            uid = st.text_input("תעודת זהות")
            upw = st.text_input("סיסמה", type="password")
            if st.form_submit_button("התחבר"):
                if mode == "מנהל" and upw == "123":
                    st.session_state.auth = "admin"; st.rerun()
                else:
                    db = st.session_state.workers_db
                    user = db[db['תז'].astype(str) == uid]
                    if not user.empty and str(user.iloc[0]['סיסמה']) == upw:
                        st.session_state.auth = "worker"; st.session_state.user = user.iloc[0]; st.rerun()
                    else: st.error("פרטים שגויים")

# --- ממשק מנהל ---
elif st.session_state.auth == "admin":
    st.sidebar.button("יציאה 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    tab1, tab2, tab3 = st.tabs(["👥 ניהול עובדים", "📥 בקשות ממתינות", "📊 דוח משמרות (Excel)"])
    
    with tab1: # ניהול עובדים
        if not st.session_state.workers_db.empty:
            for idx, row in st.session_state.workers_db.iterrows():
                cols = st.columns([3, 2, 2, 1])
                cols[0].write(f"👤 **{row.get('שם', '')}**")
                cols[1].write(f"🆔 {row.get('תז', '')}")
                cols[2].write(f"🚑 {row.get('תפקיד', '')}")
                if cols[3].button("🗑️", key=f"del_{idx}"):
                    st.session_state.workers_db = st.session_state.workers_db.drop(idx)
                    save_db(st.session_state.workers_db, W_FILE); st.rerun()
        with st.expander("➕ הוספת עובד"):
            with st.form("add"):
                n, i, p, t = st.text_input("שם מלא"), st.text_input("תז"), st.text_input("סיסמה"), st.text_input("טלפון")
                r = st.selectbox("תפקיד", ["נוער חונך", "נוער חניך", "נוער", "חובש", "חובש (משתלם)", "משתלם נהיגה", "בת שירות"])
                if st.form_submit_button("שמור"):
                    nw = pd.DataFrame([[n, i, p, r, t]], columns=st.session_state.workers_db.columns)
                    st.session_state.workers_db = pd.concat([st.session_state.workers_db, nw], ignore_index=True)
                    save_db(st.session_state.workers_db, W_FILE); st.rerun()

    with tab2: # בקשות ממתינות
        pending = st.session_state.shifts_db[st.session_state.shifts_db['סטטוס'] == "ממתין"]
        if pending.empty:
            st.write("אין בקשות ממתינות כרגע.")
        for idx, row in pending.iterrows():
            st.info(f"{row['שם_ותפקיד']} | {row['תחנה']} | {row['תאריך']} | {row['משמרת']}")
            worker = st.session_state.workers_db[st.session_state.workers_db['תז'].astype(str) == str(row['תז'])].iloc[0]
            c1, c2 = st.columns(2)
            if c1.button("אשר ✅", key=f"a{idx}"):
                st.session_state.shifts_db.at[idx, 'סטטוס'] = "מאושר ✅"
                save_db(st.session_state.shifts_db, S_FILE)
                msg = f"שלום {row['שם_ותפקיד']}, המשמרת שלך ב{row['תחנה']} בתאריך {row['תאריך']} אושרה! 🚑❤️"
                st.markdown(f'<a href="https://wa.me/{worker["טלפון"]}?text={urllib.parse.quote(msg)}" target="_blank" class="whatsapp-btn">שלח הודעת אישור ✅</a>', unsafe_allow_html=True)
                st.rerun()
            if c2.button("דחה ❌", key=f"r{idx}"):
                st.session_state.shifts_db.at[idx, 'סטטוס'] = "מבוטל ❌"
                save_db(st.session_state.shifts_db, S_FILE)
                st.rerun()

    with tab3: # דוח אקסל
        st.subheader("משמרות מאושרות (דוח להורדה)")
        approved_shifts = st.session_state.shifts_db[st.session_state.shifts_db['סטטוס'] == "מאושר ✅"]
        
        if not approved_shifts.empty:
            st.dataframe(approved_shifts[["שם_ותפקיד", "תחנה", "תאריך", "משמרת"]], use_container_width=True)
            
            # تحويل البيانات إلى CSV للتحميل
            csv = approved_shifts.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="הורד דוח משמרות לאקסל 📥",
                data=csv,
                file_name=f"mda_shifts_{datetime.now().strftime('%Y-%m-%d')}.csv",
                mime="text/csv",
            )
        else:
            st.write("אין עדיין משמרות מאושרות להצגה.")

# --- ממשק עובד ---
else:
    st.sidebar.button("התנתק 🚪", on_click=lambda: st.session_state.update({"auth": None}))
    u = st.session_state.user
    st.write(f"### שלום, {u['שם']}")
    br = st.selectbox("בחר תחנה", list(STATION_HOURS.keys()))
    with st.form("req_v9"):
        sh = st.radio("בחר משמרת", STATION_HOURS[br])
        dt = st.selectbox("בחר יום ותאריך", get_week_days())
        if st.form_submit_button("שלח בקשת משמרת 🚑❤️"):
            full = f"{u['שם']} ({u['תפקיד']})"
            ns = pd.DataFrame([[u['תז'], full, br, dt, sh, "לבן", "ממתין"]], columns=st.session_state.shifts_db.columns)
            st.session_state.shifts_db = pd.concat([st.session_state.shifts_db, ns], ignore_index=True)
            save_db(st.session_state.shifts_db, S_FILE)
            st.balloons()
            st.success("תודה! הבקשה נשלחה ❤️🚑❤️")