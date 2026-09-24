import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import os
import base64
from PIL import Image

# ==========================================
# 1. إعدادات الصفحة والأيقونة
# ==========================================
logo_file = None
for name in ["logo.jpg", "logo.jpg.jpeg", "logo.png", "logo.jpeg"]:
    if os.path.exists(name):
        logo_file = name
        break

logo_img = Image.open(logo_file) if logo_file else None

if logo_img:
    st.set_page_config(
        page_title="Focal Craft Team",
        page_icon=logo_img,
        layout="wide"
    )
else:
    st.set_page_config(
        page_title="Focal Craft Team",
        page_icon="🎬",
        layout="wide"
    )

def get_image_base64(image_path):
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

logo_base64 = get_image_base64(logo_file)

# ==========================================
# 2. قواعد البيانات (SQLite) مع إصلاح الخطأ
# ==========================================
DB_FILE = "focal_craft.db"

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            details TEXT
        )
    ''')
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        hashed_pw = hash_pass("admin123")
        c.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
                  ('admin', hashed_pw, 'Owner', 'Eng Abdelrhman Osama'))
    conn.commit()
    conn.close()

init_db()

def check_login(username, password):
    init_db()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username, role, name FROM users WHERE username = ? AND password = ?", 
              (username, hash_pass(password)))
    user = c.fetchone()
    conn.close()
    return user

# ==========================================
# 3. إدارة الجلسة واللغة (Session State)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "lang" not in st.session_state:
    st.session_state.lang = "EN"  # الافتراضي إنجليزي

# قاموس اللغات (Dictionary for Translations)
translations = {
    "EN": {
        "title": "Focal Craft Team",
        "subtitle": "Unified Company Management System",
        "username": "Username",
        "password": "Password",
        "login_btn": "Login",
        "login_success": "Logged in successfully!",
        "login_error": "Invalid username or password",
        "welcome": "Welcome",
        "role": "Role",
        "nav": "Navigation",
        "home": "Home Page",
        "cs": "Customer Service",
        "packages": "Packages Management",
        "employees": "Employees Management",
        "audit": "Accounts & Audit",
        "logout": "Logout",
        "status": "System Status",
        "active": "Active 🟢",
        "add_pkg": "Add New Package",
        "pkg_name": "Package Name",
        "price": "Price",
        "details": "Details",
        "save": "Save",
        "add_emp": "Add New Employee",
        "fullname": "Full Name",
        "emp_added": "Employee added successfully!",
        "user_exists": "Username already exists!"
    },
    "AR": {
        "title": "فوكال كرافت تيم",
        "subtitle": "نظام إدارة الشركة الموحد",
        "username": "اسم المستخدم",
        "password": "كلمة المرور",
        "login_btn": "تسجيل الدخول",
        "login_success": "تم تسجيل الدخول بنجاح!",
        "login_error": "اسم المستخدم أو كلمة المرور غير صحيحة",
        "welcome": "مرحباً بك",
        "role": "الصلاحية",
        "nav": "التنقل",
        "home": "الصفحة الرئيسية",
        "cs": "خدمة العملاء",
        "packages": "إدارة الباقات",
        "employees": "إدارة الموظفين",
        "audit": "الحسابات والتدقيق",
        "logout": "تسجيل الخروج",
        "status": "حالة النظام",
        "active": "نشط 🟢",
        "add_pkg": "إضافة باقة جديدة",
        "pkg_name": "اسم الباقة",
        "price": "السعر",
        "details": "التفاصيل",
        "save": "حفظ",
        "add_emp": "إضافة موظف جديد",
        "fullname": "الاسم الكامل",
        "emp_added": "تمت إضافة الموظف بنجاح!",
        "user_exists": "اسم المستخدم موجود بالفعل!"
    }
}

t = translations[st.session_state.lang]

# ==========================================
# 4. واجهة تسجيل الدخول (Login Screen)
# ==========================================
if not st.session_state.logged_in:
    bg_style = f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.88)), 
                    url('data:image/jpeg;base64,{logo_base64}');
        background-size: cover;
        background-position: center;
    }}
    </style>
    """
    st.markdown(bg_style, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if logo_img:
            st.image(logo_img, width=150)
        st.markdown(f"<h2 style='text-align: center; color: #f8fafc;'>{t['title']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #94a3b8;'>{t['subtitle']}</p>", unsafe_allow_html=True)
        
        # اختيار اللغة في الشاشة الرئيسية
        selected_lang = st.radio("🌐 Language / اللغة", ["English", "العربية"], horizontal=True)
        st.session_state.lang = "EN" if selected_lang == "English" else "AR"
        t = translations[st.session_state.lang]

        with st.form("login_form"):
            username = st.text_input(t["username"])
            password = st.text_input(t["password"], type="password")
            submit = st.form_submit_button(t["login_btn"], use_container_width=True)
            
            if submit:
                user = check_login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_info = {"username": user[0], "role": user[1], "name": user[2]}
                    st.success(t["login_success"])
                    st.rerun()
                else:
                    st.error(t["login_error"])

# ==========================================
# 5. الواجهة الرئيسية (Dashboard)
# ==========================================
else:
    with st.sidebar:
        if logo_img:
            st.image(logo_img, use_container_width=True)
        st.title(t["title"])
        st.write(f"{t['welcome']}: **{st.session_state.user_info['name']}**")
        st.caption(f"{t['role']}: {st.session_state.user_info['role']}")
        
        # تحويل اللغة داخل الحساب
        lang_choice = st.radio("🌐 Language / اللغة", ["English", "العربية"], 
                               index=0 if st.session_state.lang == "EN" else 1, horizontal=True)
        st.session_state.lang = "EN" if lang_choice == "English" else "AR"
        t = translations[st.session_state.lang]
        
        st.divider()
        
        role = st.session_state.user_info["role"]
        menu_options = [t["home"], t["cs"], t["packages"]]
        if role == "Owner":
            menu_options.extend([t["employees"], t["audit"]])
            
        choice = st.radio(t["nav"], menu_options)
        
        st.divider()
        if st.button(t["logout"], use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()

    # --- 1. الصفحة الرئيسية ---
    if choice in [t["home"]]:
        st.title(f"🎬 {t['home']}")
        st.write(f"{t['welcome']} {st.session_state.user_info['name']}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric(t["status"], t["active"])
        col2.metric(t["username"], st.session_state.user_info["username"])
        col3.metric(t["role"], st.session_state.user_info["role"])

    # --- 2. خدمة العملاء ---
    elif choice in [t["cs"]]:
        st.title(f"📞 {t['cs']}")

    # --- 3. إدارة الباقات ---
    elif choice in [t["packages"]]:
        st.title(f"📦 {t['packages']}")
        conn = sqlite3.connect(DB_FILE)
        
        if st.session_state.user_info["role"] == "Owner":
            with st.expander(f"➕ {t['add_pkg']}"):
                with st.form("add_package_form"):
                    p_name = st.text_input(t["pkg_name"])
                    p_price = st.number_input(t["price"], min_value=0.0)
                    p_details = st.text_area(t["details"])
                    if st.form_submit_button(t["save"]):
                        c = conn.cursor()
                        c.execute("INSERT INTO packages (name, price, details) VALUES (?, ?, ?)", 
                                  (p_name, p_price, p_details))
                        conn.commit()
                        st.success(t["save"])
                        st.rerun()
        
        df_pkgs = pd.read_sql_query("SELECT id, name, price, details FROM packages", conn)
        conn.close()
        st.dataframe(df_pkgs, use_container_width=True)

    # --- 4. إدارة الموظفين ---
    elif choice in [t["employees"]] and role == "Owner":
        st.title(f"👥 {t['employees']}")
        conn = sqlite3.connect(DB_FILE)
        
        with st.expander(f"➕ {t['add_emp']}"):
            with st.form("add_user_form"):
                u_name = st.text_input(t["fullname"])
                u_username = st.text_input(t["username"])
                u_password = st.text_input(t["password"], type="password")
                u_role = st.selectbox(t["role"], ["Customer Service", "Editor", "Moderator", "Owner"])
                if st.form_submit_button(t["save"]):
                    try:
                        c = conn.cursor()
                        c.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
                                  (u_username, hash_pass(u_password), u_role, u_name))
                        conn.commit()
                        st.success(t["emp_added"])
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(t["user_exists"])
        
        df_users = pd.read_sql_query("SELECT id, name, username, role FROM users", conn)
        conn.close()
        st.dataframe(df_users, use_container_width=True)

    # --- 5. الحسابات والتدقيق ---
    elif choice in [t["audit"]] and role == "Owner":
        st.title(f"📊 {t['audit']}")
