import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from PIL import Image

# 1. הגדרות דף
st.set_page_config(page_title='מערכת שיבוץ אשכול', layout='wide', page_icon='🚑')

# 2. ניהול קבצים עם הגנה מפני שגיאות (Fix for Red Error)
W_FILE, S_FILE = "workers_final.csv", "shifts_final.csv"
PIC_DIR = "profile_pics"
if not os.path.exists(PIC_DIR): os.makedirs(PIC_DIR)

# עמודות נדרשות
W_COLS = ["שם", "תז", "סיסמה", "תפקיד", "טלפון", "תמונה"]
S_COLS = ["תז", "שם", "טלפון", "תחנה", "תאריך", "משמרת", "תפקיד", "צבע", "סטטוס"]

def load_db(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        # בדיקה אם חסרות עמודות והוספתן אוטומטית (מונע את השגיאה האדומה)
        for col in cols:
            if col not in df.columns:
                df[col] = ""
        return df[cols] # מחזיר רק את העמודות הנכונות בסדר הנכון
    else:
        return pd.DataFrame(columns=cols)

def save_db(df, file):
    df.to_csv(file, index=False, encoding='utf-8-sig')

# אתחול מסדי נתונים
if 'workers_db' not in st.session_state: 
    st.session_state.workers_db = load_db(W_FILE, W_COLS)
if 'shifts_db' not in st.session_state: 
    st.session_state.shifts_db = load_db(S_FILE, S_COLS)

# 3. הגדרות מערכת
ADMIN_SUPER = {"admin": "123"} # זמני עד שתביא לי את השמות
ADMIN_NORMAL = {}

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

# 4. עיצוב ממשק
is_logged_in = 'auth' in st.session_state and st.session_state.auth is not None
st.markdown(f"""
    <style>
    .stApp {{ background-color: {"#f4f7f9" if is_logged_in else "#1a3a6d"}; }}
    .stMarkdown p, label {{ color: {"#000000" if is_logged_in else "#ffffff"} !important; font-weight: bold; }}
    .main-header {{ background-color: #000000; padding: 20px; border-radius: 15px; border-bottom: 6px solid #d32f2f; text-align: center; margin-bottom: 20px; }}
    .main-header h1 {{ color: #ffffff !important; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1>🚑 מערכת שיבוץ אשכול חורה מיתר לקיה</h1></div>', unsafe_allow_html=True)

# --- לוגיקה של דפים ---
if not is_logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mode = st.radio("בחר סוג כניסה:", ["עובד", "מנהל"], horizontal=True)
        with st.form("login"):
            u_in = st.text_input("שם משתמש / תעודת זהות")
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
else:
    # כאן נכנס הקוד של המנהל והעובד (הוא תקין ולא השתנה)
    # כדי לשמור על קובץ קצר, אני מציע שתנסה להריץ את זה קודם ולראות אם השגיאה האדומה נעלמה
    st.sidebar.button("התנתק", on_click=lambda: st.session_state.update({"auth": None}))
    st.write(f"שלום {st.session_state.get('admin_name', 'משתמש')}")
    # ... שאר הקוד המקורי ...
