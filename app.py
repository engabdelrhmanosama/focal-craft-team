import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import os
import base64
from PIL import Image

# ==========================================
# 1. تحميل صورة اللوجو وإعدادات الصفحة
# ==========================================
try:
    logo = Image.open("logo.jpg")
except Exception:
    try:
        logo = Image.open("logo.jpg.jpeg")
    except Exception:
        logo = None

# إعدادات الصفحة (يجب أن تكون في البداية)
if logo:
    st.set_page_config(
        page_title="فوكال كرافت تيم - Focal Craft Team",
        page_icon=logo,
        layout="wide"
    )
else:
    st.set_page_config(
        page_title="فوكال كرافت تيم - Focal Craft Team",
        page_icon="🎬",
        layout="wide"
    )

# دالة تحويل الصورة إلى Base64 للخلفية
def get_image_base64(image_path):
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

logo_file = "logo.jpg" if os.path.exists("logo.jpg") else ("logo.jpg.jpeg" if os.path.exists("logo.jpg.jpeg") else None)
logo_base64 = get_image_base64(logo_file) if logo_file else ""

# ==========================================
# 2. قواعد البيانات (SQLite)
# ==========================================
DB_FILE = "focal_craft.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # جدول المستخدمين
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL
        )
    ''')
    
    # جدول الباقات
    c.execute('''
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            details TEXT
        )
    ''')
    
    # إنشاء حساب Owner افتراضي إذا لم يكن موجوداً
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
                  ('admin', hashed_pw, 'Owner', 'باشمهندس عبد الرحمن'))
    
    conn.commit()
    conn.close()

init_db()

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, role, name FROM users WHERE username = ? AND password = ?", 
              (username, hash_pass(password)))
    user = c.fetchone()
    conn.close()
    return user

# ==========================================
# 3. إدارة الجلسة (Session State)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# ==========================================
# 4. واجهة تسجيل الدخول (Login Screen)
# ==========================================
if not st.session_state.logged_in:
    # خلفية وتنسيق شاشة تسجيل الدخول
    bg_style = f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.85)), 
                    url('data:image/jpeg;base64,{logo_base64}');
        background-size: cover;
        background-position: center;
    }}
    .login-card {{
        background-color: rgba(30, 41, 59, 0.9);
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        max-width: 400px;
        margin: auto;
        color: white;
        text-align: center;
    }}
    </style>
    """
    st.markdown(bg_style, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if logo:
            st.image(logo, width=150)
        st.markdown("<h2 style='text-align: center; color: #f8fafc;'>Focal Craft Team</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>نظام إدارة الشركة الموحد</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password")
            submit = st.form_submit_button("تسجيل الدخول", use_container_width=True)
            
            if submit:
                user = check_login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_info = {"username": user[0], "role": user[1], "name": user[2]}
                    st.success("تم تسجيل الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

# ==========================================
# 5. الواجهة الرئيسية للبرنامج (Dashboard)
# ==========================================
else:
    # القائمة الجانبية (Sidebar)
    with st.sidebar:
        if logo:
            st.image(logo, use_container_width=True)
        st.title("Focal Craft Team")
        st.write(f"مرحباً بك: **{st.session_state.user_info['name']}**")
        st.caption(f"الصلاحية: {st.session_state.user_info['role']}")
        st.divider()
        
        # خيارات القائمة حسب الصلاحيات
        role = st.session_state.user_info["role"]
        menu_options = ["الصفحة الرئيسية", "خدمة العملاء", "إدارة الباقات"]
        if role == "Owner":
            menu_options.extend(["إدارة الموظفين", "الحسابات والتدقيق"])
            
        choice = st.radio("الانتقال إلى", menu_options)
        
        st.divider()
        if st.button("تسجيل الخروج", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()

    # --- 1. الصفحة الرئيسية ---
    if choice == "الصفحة الرئيسية":
        st.title("🎬 لوحة التحكم الرئيسية")
        st.write("أهلاً بك في نظام إدارة شركة **Focal Craft**.")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("حالة النظام", "نشط 🟢")
        col2.metric("المستخدم الحالي", st.session_state.user_info["name"])
        col3.metric("الصلاحية", st.session_state.user_info["role"])

    # --- 2. خدمة العملاء ---
    elif choice == "خدمة العملاء":
        st.title("📞 قسم خدمة العملاء")
        st.write("إدارة طلبات العملاء والاستفسارات.")

    # --- 3. إدارة الباقات ---
    elif choice == "إدارة الباقات":
        st.title("📦 إدارة الباقات والخدمات")
        
        conn = sqlite3.connect(DB_FILE)
        
        # إضافة باقة جديدة (للمالك فقط)
        if st.session_state.user_info["role"] == "Owner":
            with st.expander("➕ إضافة باقة جديدة"):
                with st.form("add_package_form"):
                    p_name = st.text_input("اسم الباقة")
                    p_price = st.number_input("السعر", min_value=0.0)
                    p_details = st.text_area("تفاصيل الباقة")
                    if st.form_submit_button("حفظ الباقة"):
                        c = conn.cursor()
                        c.execute("INSERT INTO packages (name, price, details) VALUES (?, ?, ?)", 
                                  (p_name, p_price, p_details))
                        conn.commit()
                        st.success("تمت إضافة الباقة بنجاح!")
                        st.rerun()
        
        # عرض الباقات
        df_pkgs = pd.read_sql_query("SELECT id AS 'المعرف', name AS 'اسم الباقة', price AS 'السعر', details AS 'التفاصيل' FROM packages", conn)
        conn.close()
        st.dataframe(df_pkgs, use_container_width=True)

    # --- 4. إدارة الموظفين (للمالك فقط) ---
    elif choice == "إدارة الموظفين" and role == "Owner":
        st.title("👥 إدارة الموظفين والحسابات")
        
        conn = sqlite3.connect(DB_FILE)
        
        with st.expander("➕ إضافة موظف جديد"):
            with st.form("add_user_form"):
                u_name = st.text_input("الاسم الكامل")
                u_username = st.text_input("اسم المستخدم (Username)")
                u_password = st.text_input("كلمة المرور", type="password")
                u_role = st.selectbox("الصلاحية", ["Customer Service", "Editor", "Moderator", "Owner"])
                if st.form_submit_button("إضافة الموظف"):
                    try:
                        c = conn.cursor()
                        c.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
                                  (u_username, hash_pass(u_password), u_role, u_name))
                        conn.commit()
                        st.success("تمت إضافة الموظف بنجاح!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("اسم المستخدم موجود بالفعل!")
        
        df_users = pd.read_sql_query("SELECT id AS 'المعرف', name AS 'الاسم', username AS 'اسم المستخدم', role AS 'الصلاحية' FROM users", conn)
        conn.close()
        st.dataframe(df_users, use_container_width=True)

    # --- 5. الحسابات والتدقيق (للمالك فقط) ---
    elif choice == "الحسابات والتدقيق" and role == "Owner":
        st.title("📊 الحسابات والتقارير الشهرية")
        st.write("مراجعة الإيرادات والتدقيق المالي.")
