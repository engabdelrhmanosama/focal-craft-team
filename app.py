import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import base64
import json
import re
import calendar
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO

# ==========================================
# 1. Page Config & Ultra Dark Theme Setup
# ==========================================
logo_path = None
for name in ["logo.jpg", "logo.jpg.jpeg", "logo.png", "logo.jpeg"]:
    if os.path.exists(name):
        logo_path = name
        break

logo_img = None
if logo_path:
    try:
        logo_img = Image.open(logo_path)
    except Exception:
        logo_img = None

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

# Create Uploads Directory if it doesn't exist
UPLOAD_DIR = "uploaded_avatars"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def save_uploaded_file(uploaded_file, prefix="emp"):
    if uploaded_file is not None:
        file_ext = os.path.splitext(uploaded_file.name)[1]
        file_name = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return ""

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Cairo', 'Inter', sans-serif;
            background-color: #0b0f19 !important;
            color: #f1f5f9 !important;
        }

        .stApp {
            background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #0f172a 100%) !important;
        }

        .top-navbar-container {
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 18px;
            padding: 16px 24px;
            margin-bottom: 25px;
            backdrop-filter: blur(16px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.1);
        }

        .emp-card-pro {
            background: rgba(17, 24, 39, 0.75) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 16px !important;
            padding: 22px !important;
            margin-bottom: 20px !important;
            box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5) !important;
            backdrop-filter: blur(12px) !important;
            transition: all 0.3s ease !important;
        }

        .emp-card-pro:hover {
            border-color: rgba(239, 68, 68, 0.5) !important;
            transform: translateY(-4px) !important;
            box-shadow: 0 14px 40px -5px rgba(239, 68, 68, 0.2) !important;
        }

        .emp-badge {
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 700;
            display: inline-block;
        }

        .emp-avatar-img {
            width: 75px;
            height: 75px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #ef4444;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9)) !important;
            padding: 18px !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
        }

        div[data-testid="stMetricLabel"] {
            color: #94a3b8 !important;
            font-size: 0.9rem !important;
            font-weight: 600 !important;
        }

        div[data-testid="stMetricValue"] {
            color: #f8fafc !important;
            font-weight: 800 !important;
        }

        .stButton>button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.25s ease !important;
        }

        .stButton>button[kind="primary"] {
            background: linear-gradient(135deg, #ef4444, #dc2626) !important;
            border: none !important;
            color: white !important;
            box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3) !important;
        }

        .stButton>button[kind="primary"]:hover {
            background: linear-gradient(135deg, #f87171, #ef4444) !important;
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.5) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: rgba(15, 23, 42, 0.6);
            padding: 6px;
            border-radius: 10px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: 600;
            color: #94a3b8;
        }

        .stTabs [aria-selected="true"] {
            background-color: #ef4444 !important;
            color: #ffffff !important;
        }

        .stTextInput>div>div>input, .stSelectbox>div>div, .stTextArea>div>div>textarea {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 8px !important;
        }

        .stDataFrame {
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 10px !important;
            overflow: hidden !important;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# 2. Database Connection & Enhanced Schema
# ==========================================
DB_FILE = "focal_craft.db"

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    
    # Enhanced Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            salary REAL DEFAULT 0.0,
            phone TEXT DEFAULT '',
            national_id TEXT DEFAULT '',
            address TEXT DEFAULT '',
            photo_path TEXT DEFAULT ''
        )
    ''')
    
    # Packages Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            details TEXT,
            duration_days INTEGER DEFAULT 30,
            editor_tasks TEXT DEFAULT '',
            social_tasks TEXT DEFAULT '',
            web_tasks TEXT DEFAULT ''
        )
    ''')
    
    # Enhanced Clients Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            phone TEXT,
            national_id TEXT DEFAULT '',
            address TEXT DEFAULT '',
            photo_path TEXT DEFAULT '',
            package_id INTEGER,
            notes TEXT,
            tasks_status TEXT DEFAULT '{}',
            created_at TEXT,
            FOREIGN KEY (package_id) REFERENCES packages (id)
        )
    ''')
    
    # Assigned Tasks Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS assigned_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            assigned_role TEXT NOT NULL,
            assigned_user_name TEXT DEFAULT 'Auto Assigned',
            task_description TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TEXT,
            completed_at TEXT DEFAULT '-'
        )
    ''')
    
    # Expenses Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT,
            added_by TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Incomes Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS incomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            package_name TEXT NOT NULL,
            amount REAL NOT NULL,
            added_by TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Cameras Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cam_name TEXT NOT NULL,
            stream_url TEXT NOT NULL,
            location TEXT DEFAULT 'Main Office'
        )
    ''')

    # Attendance Records Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id INTEGER NOT NULL,
            emp_name TEXT,
            date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            status TEXT DEFAULT 'Present',
            FOREIGN KEY (emp_id) REFERENCES users (id)
        )
    ''')
    
    # Auto Migration Checks
    def add_col_if_not_exists(table, col, col_type):
        c.execute(f"PRAGMA table_info({table})")
        cols = [column[1] for column in c.fetchall()]
        if col not in cols:
            try:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            except Exception:
                pass

    add_col_if_not_exists("users", "phone", "TEXT DEFAULT ''")
    add_col_if_not_exists("users", "national_id", "TEXT DEFAULT ''")
    add_col_if_not_exists("users", "address", "TEXT DEFAULT ''")
    add_col_if_not_exists("users", "photo_path", "TEXT DEFAULT ''")

    add_col_if_not_exists("clients", "national_id", "TEXT DEFAULT ''")
    add_col_if_not_exists("clients", "address", "TEXT DEFAULT ''")
    add_col_if_not_exists("clients", "photo_path", "TEXT DEFAULT ''")

    # Default Owner User
    owner_username = "Eng Abdelrhman Osama"
    default_password = hash_pass("#Bedo-1428")
    
    c.execute("SELECT * FROM users WHERE role = 'Owner'")
    owner_user = c.fetchone()
    
    if not owner_user:
        c.execute("INSERT INTO users (username, password, role, name, salary) VALUES (?, ?, ?, ?, ?)",
                  (owner_username, default_password, 'Owner', owner_username, 0.0))
    conn.commit()
    return conn

def check_login(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT username, role, name FROM users WHERE username = ? AND password = ?", 
              (username, hash_pass(password)))
    user = c.fetchone()
    conn.close()
    return user

def parse_and_split_tasks(task_text, default_label="Task"):
    tasks_list = []
    if not task_text or not task_text.strip():
        return tasks_list
    
    lines = [line.strip() for line in task_text.replace("\n", ",").split(",") if line.strip()]
    
    for line in lines:
        match = re.search(r'(\d+)', line)
        if match:
            count = int(match.group(1))
            clean_desc = re.sub(r'\d+', '', line).strip()
            if not clean_desc:
                clean_desc = default_label
            
            count = min(count, 100)
            for i in range(1, count + 1):
                tasks_list.append(f"{clean_desc} #{i}")
        else:
            tasks_list.append(line)
            
    return tasks_list

def find_matching_employee(target_role, conn):
    c = conn.cursor()
    users = c.execute("SELECT name, role FROM users").fetchall()
    target_role_lower = target_role.lower()
    
    for emp_name, emp_role in users:
        emp_role_lower = emp_role.lower()
        if target_role_lower in emp_role_lower or emp_role_lower in target_role_lower:
            return emp_name
        if "editor" in target_role_lower and ("مونتاج" in emp_role_lower or "إيديت" in emp_role_lower or "video" in emp_role_lower):
            return emp_name
        if "social" in target_role_lower and ("سوشيال" in emp_role_lower or "ميديا" in emp_role_lower or "social" in emp_role_lower):
            return emp_name
        if "web" in target_role_lower and ("مواقع" in emp_role_lower or "ويب" in emp_role_lower or "web" in emp_role_lower or "designer" in emp_role_lower):
            return emp_name
            
    return "فريق العمل (توزيع تلقائي)"

# ==========================================
# 3. Session State & Multi-Language Dictionary
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "lang" not in st.session_state:
    st.session_state.lang = "AR"

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
        "home": "Home Page",
        "my_tasks": "My Assigned Tasks",
        "cs": "Clients & Services Tracking",
        "expenses": "Expenses & Sheet Upload",
        "packages": "Packages Management",
        "employees": "Employee Hub & Tasks",
        "cameras": "CCTV Surveillance",
        "attendance": "Fingerprint Attendance",
        "audit": "Financial Audit & Sheet",
        "logout": "Logout",
        "status": "System Status",
        "active": "Active 🟢",
        "add_pkg": "Add New Package",
        "pkg_name": "Package Name",
        "price": "Price",
        "pkg_duration": "Package Duration (Days)",
        "details": "General Package Details",
        "editor_tasks": "Editor Tasks",
        "social_tasks": "Social Media Tasks",
        "web_tasks": "Web Designer Tasks",
        "save": "Save",
        "add_emp": "➕ Add New Employee",
        "add_emp_modal_title": "👤 Add New Employee",
        "fullname": "Full Name",
        "emp_added": "Employee added successfully!",
        "user_exists": "Username or ID already exists!",
        "delete": "Delete Account",
        "edit": "Edit Details & Salary",
        "add_client": "Add New Client",
        "client_name": "Client Name",
        "phone": "Phone Number",
        "national_id": "National ID",
        "address": "Address",
        "photo": "Upload Avatar / Photo",
        "select_package": "Select Package",
        "notes": "Notes",
        "client_added": "Client added, income logged & tasks assigned!",
        "clients_list": "Subscribed Clients List",
        "track_services": "Track Services",
        "select_client_track": "Select client:",
        "save_tasks": "Save Service Status 💾",
        "tasks_saved": "Client service status updated!",
        "no_packages_err": "Please contact owner to add packages first!",
        "exp_title": "Expense Title",
        "amount": "Amount",
        "category": "Category",
        "log_exp_btn": "Log Expense",
        "exp_saved": "Expense logged successfully!",
        "upload_exp_sheet": "📥 Upload Monthly Expenses Sheet (Excel/CSV)",
        "total_exp": "Total Expenses",
        "total_inc": "Total Revenue",
        "net_profit": "Net Profit",
        "export_excel": "📥 Export Monthly Financial Sheet",
        "tab_emp_mgmt": "👤 Employee Management",
        "tab_emp_tasks": "📊 Task Completion & Timeline Tracking",
        "search_emp_placeholder": "🔍 Search employee...",
        "emp_id_label": "Employee ID"
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
        "home": "الصفحة الرئيسية",
        "my_tasks": "مهامي والشغل المطلوب",
        "cs": "إدارة العملاء والبيانات",
        "expenses": "المصروفات ورفع الشيتات",
        "packages": "إدارة الباقات",
        "employees": "الموظفين والمرتبات والمهام",
        "cameras": "كاميرات المراقبة",
        "attendance": "جهاز البصمة والحضور",
        "audit": "شيت الحسابات والتدقيق المالي",
        "logout": "تسجيل الخروج",
        "status": "حالة النظام",
        "active": "نشط 🟢",
        "add_pkg": "إضافة باقة جديدة",
        "pkg_name": "اسم الباقة",
        "price": "السعر",
        "pkg_duration": "مدة الباقة (بالأيام)",
        "details": "تفاصيل الباقة العامة",
        "editor_tasks": "مهام المونتير",
        "social_tasks": "مهام السوشيال ميديا",
        "web_tasks": "مهام مصمم المواقع",
        "save": "حفظ",
        "add_emp": "➕ إضافة موظف جديد",
        "add_emp_modal_title": "👤 إضافة موظف جديد",
        "fullname": "الاسم الكامل",
        "emp_added": "تمت إضافة الموظف بنجاح!",
        "user_exists": "اسم المستخدم أو الرقم التعريفي موجود بالفعل!",
        "delete": "حذف حساب الموظف",
        "edit": "تعديل البيانات والمرتب",
        "add_client": "إضافة عميل جديد",
        "client_name": "اسم العميل",
        "phone": "رقم الهاتف",
        "national_id": "الرقم القومي",
        "address": "العنوان",
        "photo": "رفع صورة شخصية",
        "select_package": "اختر الباقة",
        "notes": "ملاحظات",
        "client_added": "تمت إضافة العميل، وتوزيع المهام بنجاح!",
        "clients_list": "قائمة العملاء المشتركين",
        "track_services": "متابعة تنفيذ خدمات الباقة",
        "select_client_track": "اختر العميل لمتابعة الخدمات:",
        "save_tasks": "حفظ التحديثات 💾",
        "tasks_saved": "تم حفظ حالة الخدمات بنجاح!",
        "no_packages_err": "يرجى التواصل مع المالك لإضافة باقات أولاً!",
        "exp_title": "بيان المصروف",
        "amount": "المبلغ",
        "category": "القسم",
        "log_exp_btn": "تسجيل المصروف",
        "exp_saved": "تم تسجيل المصروف بنجاح!",
        "upload_exp_sheet": "📥 رفع وتطبيق شيت مصروفات شهري (Excel / CSV)",
        "total_exp": "إجمالي المصروفات",
        "total_inc": "إجمالي الإيرادات",
        "net_profit": "صافي أرباح الشركة",
        "export_excel": "📥 سحب شيت المصروفات المالي (1 لـ 30/31)",
        "tab_emp_mgmt": "👤 إدارة الموظفين والمرتبات والبيانات",
        "tab_emp_tasks": "📊 متابعة إنجاز مهام الموظفين والتوقيت",
        "search_emp_placeholder": "🔍 ابحث بالاسم، ID، الهاتف، القومي...",
        "emp_id_label": "الرقم التعريفي (ID الموظف)"
    }
}

t = translations[st.session_state.lang]

# ==========================================
# 4. Login Interface
# ==========================================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if logo_img:
            st.image(logo_img, width=150)
        st.markdown(f"<h2 style='text-align: center; font-weight: 800; color: #f8fafc;'>{t['title']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #94a3b8;'>{t['subtitle']}</p>", unsafe_allow_html=True)
        
        selected_lang = st.radio("🌐 Language / اللغة", ["العربية", "English"], 
                                 index=0 if st.session_state.lang == "AR" else 1, horizontal=True)
        st.session_state.lang = "AR" if selected_lang == "العربية" else "EN"
        t = translations[st.session_state.lang]

        with st.form("login_form"):
            username = st.text_input(t["username"])
            password = st.text_input(t["password"], type="password")
            submit = st.form_submit_button(t["login_btn"], use_container_width=True, type="primary")
            
            if submit:
                user = check_login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_info = {"username": user[0], "role": user[1], "name": user[2]}
                    st.session_state.active_nav = t["home"]
                    st.success(t["login_success"])
                    st.rerun()
                else:
                    st.error(t["login_error"])

# ==========================================
# 5. Main Dashboard & Navigation
# ==========================================
else:
    st.markdown("<div class='top-navbar-container'>", unsafe_allow_html=True)
    top_col_a, top_col_b = st.columns([1, 5])
    
    with top_col_a:
        if logo_img:
            st.image(logo_img, width=110)
        else:
            st.markdown("### 🎬 Focal Craft")
            
    with top_col_b:
        role = st.session_state.user_info["role"]
        
        nav_items = [t["home"], t["my_tasks"]]
        if role in ["Owner", "Manager"]:
            nav_items.append(t["employees"])
        nav_items.extend([t["cs"], t["expenses"], t["packages"], t["cameras"], t["attendance"]])
        if role == "Owner":
            nav_items.append(t["audit"])

        nav_cols = st.columns(len(nav_items) + 2)
        
        if 'active_nav' not in st.session_state:
            st.session_state.active_nav = t["home"]

        for idx, item in enumerate(nav_items):
            with nav_cols[idx]:
                btn_type = "primary" if st.session_state.active_nav == item else "secondary"
                if st.button(item, key=f"top_nav_{idx}", type=btn_type, use_container_width=True):
                    st.session_state.active_nav = item
                    st.rerun()
                    
        with nav_cols[-2]:
            lang_choice = st.selectbox("", ["العربية", "English"], 
                                      index=0 if st.session_state.lang == "AR" else 1, label_visibility="collapsed")
            if (lang_choice == "English" and st.session_state.lang != "EN") or (lang_choice == "العربية" and st.session_state.lang != "AR"):
                st.session_state.lang = "EN" if lang_choice == "English" else "AR"
                st.rerun()
                
        with nav_cols[-1]:
            if st.button("🚪 " + t["logout"], type="secondary", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_info = None
                st.rerun()
                
    st.markdown("</div>", unsafe_allow_html=True)

    choice = st.session_state.active_nav

    # --- 1. Home Page ---
    if choice == t["home"]:
        st.title(f"🎬 {t['home']}")
        st.write(f"{t['welcome']} **{st.session_state.user_info['name']}**")
        
        col1, col2, col3 = st.columns(3)
        col1.metric(t["status"], t["active"])
        col2.metric(t["username"], st.session_state.user_info["username"])
        col3.metric(t["role"], st.session_state.user_info["role"])

    # --- 2. My Assigned Tasks ---
    elif choice == t["my_tasks"]:
        st.title(f"📋 {t['my_tasks']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        if role != "Owner":
            tasks_df = pd.read_sql_query("SELECT * FROM assigned_tasks WHERE assigned_role = ? OR assigned_user_name = ?", conn, params=(role, st.session_state.user_info['name']))
        else:
            tasks_df = pd.read_sql_query("SELECT * FROM assigned_tasks", conn)

        pending_tasks = tasks_df[tasks_df["status"].isin(["Pending", "قيد التنفيذ"])] if not tasks_df.empty else pd.DataFrame()
        completed_tasks = tasks_df[tasks_df["status"].isin(["Completed ✅", "مكتمل ✅"])] if not tasks_df.empty else pd.DataFrame()

        tab1, tab2 = st.tabs(["⏳ مهام قيد التنفيذ", "✅ مهام تم إنجازها"])

        with tab1:
            if pending_tasks.empty:
                st.info("لا توجد مهام معلقة مطلوب تنفيذها حالياً! 🎉")
            else:
                for idx, row in pending_tasks.iterrows():
                    assigned_person = row.get('assigned_user_name', 'Auto Assigned')
                    with st.expander(f"📌 العميل: {row['client_name']} - {row['task_description']} ({assigned_person})"):
                        st.write(f"**تفاصيل المهمة:** {row['task_description']}")
                        st.write(f"**التخصص المطلوب:** {row['assigned_role']}")
                        st.write(f"**الموظف المسؤول:** {assigned_person}")
                        st.write(f"**تاريخ التكليف:** {row['created_at']}")
                        
                        if st.button("تحديد كـ مكتمل ✅", key=f"task_done_{row['id']}", type="primary"):
                            c.execute("UPDATE assigned_tasks SET status = 'Completed ✅', completed_at = ? WHERE id = ?",
                                      (datetime.now().strftime("%Y-%m-%d %H:%M"), row['id']))
                            conn.commit()
                            st.success("تم تحديث حالة التاسك وإنجازه بنجاح! 🚀")
                            st.rerun()

        with tab2:
            if completed_tasks.empty:
                st.caption("لم يتم إنجاز مهام بعد.")
            else:
                st.dataframe(completed_tasks[["client_name", "assigned_role", "assigned_user_name", "task_description", "completed_at"]], use_container_width=True)
                
        conn.close()

    # --- 3. Employee Hub (With Full Details & Photo Upload) ---
    elif choice == t.get("employees") and role in ["Owner", "Manager"]:
        st.title(f"👥 {t['employees']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        tab_emp_mgmt, tab_emp_tasks = st.tabs([t["tab_emp_mgmt"], t["tab_emp_tasks"]])

        with tab_emp_mgmt:
            col_head1, col_head2 = st.columns([3, 1])
            with col_head1:
                st.subheader("📋 فريق العمل والبيانات الشخصية")
            with col_head2:
                with st.popover(t["add_emp"], use_container_width=True):
                    st.markdown(f"### {t['add_emp_modal_title']}")
                    with st.form("quick_add_emp"):
                        u_custom_id = st.number_input(f"{t['emp_id_label']} (مخصص)", min_value=1, step=1, value=None)
                        u_fullname = st.text_input(t["fullname"])
                        u_username = st.text_input(t["username"])
                        u_password = st.text_input(t["password"], type="password")
                        u_phone = st.text_input(t["phone"])
                        u_national_id = st.text_input(t["national_id"])
                        u_address = st.text_input(t["address"])
                        u_photo = st.file_uploader(t["photo"], type=["jpg", "png", "jpeg"])
                        u_role_preset = st.selectbox(t["role"], ["Owner", "Manager", "Editor", "Social Media Specialist", "Web Designer", "Other / Custom"])
                        
                        if "Custom" in u_role_preset or "أخرى" in u_role_preset:
                            u_role_custom = st.text_input("المسمى الوظيفي المخصص:")
                            final_role = u_role_custom.strip() if u_role_custom.strip() != "" else "Employee"
                        else:
                            final_role = u_role_preset
                            
                        u_salary = st.number_input(f"{t['salary_txt']} (EGP)", min_value=0.0, step=500.0)

                        if st.form_submit_button(f"{t['save']} 🚀", use_container_width=True, type="primary"):
                            if u_fullname and u_username and u_password:
                                try:
                                    photo_path = save_uploaded_file(u_photo, prefix="emp") if u_photo else ""
                                    if u_custom_id:
                                        c.execute("""
                                            INSERT INTO users (id, username, password, role, name, salary, phone, national_id, address, photo_path) 
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (int(u_custom_id), u_username, hash_pass(u_password), final_role, u_fullname, u_salary, u_phone, u_national_id, u_address, photo_path))
                                    else:
                                        c.execute("""
                                            INSERT INTO users (username, password, role, name, salary, phone, national_id, address, photo_path) 
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (u_username, hash_pass(u_password), final_role, u_fullname, u_salary, u_phone, u_national_id, u_address, photo_path))
                                    conn.commit()
                                    st.success(t["emp_added"])
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error(t["user_exists"])
                            else:
                                st.error("يرجى ملء جميع الحقول المطلوبة.")

            search_query = st.text_input("", placeholder=t["search_emp_placeholder"])
            all_users = c.execute("SELECT id, name, username, role, salary, phone, national_id, address, photo_path FROM users").fetchall()

            if search_query.strip() != "":
                q = search_query.strip().lower()
                filtered_users = [
                    u for u in all_users 
                    if q in str(u[0]).lower() or q in u[1].lower() or q in u[2].lower() or q in str(u[5]).lower() or q in str(u[6]).lower()
                ]
            else:
                filtered_users = all_users

            st.divider()

            if not filtered_users:
                st.info("لم يتم العثور على نتائج للبحث.")
            else:
                cols_per_row = 3
                for i in range(0, len(filtered_users), cols_per_row):
                    row_users = filtered_users[i:i+cols_per_row]
                    cols = st.columns(cols_per_row)
                    
                    for idx, user_data in enumerate(row_users):
                        u_id, u_name, u_uname, u_role, u_sal, u_ph, u_nid, u_addr, u_pic = user_data
                        
                        img_html = ""
                        if u_pic and os.path.exists(u_pic):
                            b64 = get_image_base64(u_pic)
                            img_html = f'<img src="data:image/jpeg;base64,{b64}" class="emp-avatar-img"/>'
                        else:
                            img_html = f'<div class="emp-avatar-img" style="background:#334155; display:flex; align-items:center; justify-content:center; font-size:2rem; color:#94a3b8;">👤</div>'

                        with cols[idx]:
                            st.markdown(f"""
                            <div class="emp-card-pro">
                                <div style="display:flex; justify-content:space-between; align-items:center; gap:10px;">
                                    <div>
                                        <h3 style="margin:0; color:#f8fafc;">{u_name}</h3>
                                        <span class="emp-badge">ID #{u_id}</span>
                                    </div>
                                    {img_html}
                                </div>
                                <hr style="border-color: rgba(255,255,255,0.08); margin: 12px 0;">
                                <p style="margin:4px 0;">💼 <b>الوظيفة:</b> <code style='color:#74b9ff;'>{u_role}</code></p>
                                <p style="margin:4px 0;">💰 <b>المرتب:</b> <span style='color:#2ecc71; font-weight:700;'>{u_sal:,.2f} EGP</span></p>
                                <p style="margin:4px 0;">📱 <b>الهاتف:</b> {u_ph if u_ph else 'غير مسجل'}</p>
                                <p style="margin:4px 0;">🪪 <b>الرقم القومي:</b> {u_nid if u_nid else 'غير مسجل'}</p>
                                <p style="margin:4px 0;">📍 <b>العنوان:</b> {u_addr if u_addr else 'غير مسجل'}</p>
                            </div>
                            """, unsafe_allow_html=True)

                            with st.popover(f"⚙️ تعديل / خيارات ({u_name})", use_container_width=True):
                                st.markdown(f"#### تعديل بيانات {u_name}")
                                
                                with st.form(f"edit_form_{u_id}"):
                                    e_fullname = st.text_input(t["fullname"], value=u_name)
                                    e_username = st.text_input(t["username"], value=u_uname)
                                    e_role = st.text_input("الوظيفة", value=u_role)
                                    e_salary = st.number_input("المرتب", value=float(u_sal if u_sal else 0.0), step=500.0)
                                    e_phone = st.text_input(t["phone"], value=u_ph if u_ph else "")
                                    e_nid = st.text_input(t["national_id"], value=u_nid if u_nid else "")
                                    e_addr = st.text_input(t["address"], value=u_addr if u_addr else "")
                                    e_photo = st.file_uploader("تحديث الصورة", type=["jpg", "png", "jpeg"])
                                    e_password = st.text_input("كلمة سر جديدة (اختياري)", type="password")

                                    if st.form_submit_button("حفظ التعديلات 💾", use_container_width=True, type="primary"):
                                        try:
                                            new_pic_path = save_uploaded_file(e_photo, prefix="emp") if e_photo else u_pic
                                            if e_password.strip() != "":
                                                c.execute("""
                                                    UPDATE users SET username = ?, name = ?, role = ?, salary = ?, phone = ?, national_id = ?, address = ?, photo_path = ?, password = ? 
                                                    WHERE id = ?
                                                """, (e_username, e_fullname, e_role, e_salary, e_phone, e_nid, e_addr, new_pic_path, hash_pass(e_password), u_id))
                                            else:
                                                c.execute("""
                                                    UPDATE users SET username = ?, name = ?, role = ?, salary = ?, phone = ?, national_id = ?, address = ?, photo_path = ? 
                                                    WHERE id = ?
                                                """, (e_username, e_fullname, e_role, e_salary, e_phone, e_nid, e_addr, new_pic_path, u_id))
                                            conn.commit()
                                            st.success("تم تحديث بيانات الموظف بنجاح!")
                                            st.rerun()
                                        except sqlite3.IntegrityError:
                                            st.error("اسم المستخدم مكرر!")

                                st.divider()
                                if u_uname != st.session_state.user_info["username"]:
                                    if st.button("🗑️ حذف الموظف نهائياً", key=f"del_{u_id}", type="primary", use_container_width=True):
                                        c.execute("DELETE FROM users WHERE id = ?", (u_id,))
                                        conn.commit()
                                        st.success("تم الحذف بنجاح!")
                                        st.rerun()

        with tab_emp_tasks:
            st.subheader(t["task_overview"])
            tasks_df = pd.read_sql_query("SELECT * FROM assigned_tasks", conn)
            
            if tasks_df.empty:
                st.info("لا توجد مهام مسجلة حتى الآن.")
            else:
                col_m1, col_m2, col_m3 = st.columns(3)
                tot = len(tasks_df)
                dn = len(tasks_df[tasks_df["status"].isin(["Completed ✅", "مكتمل ✅"])])
                pn = tot - dn

                col_m1.metric("إجمالي المهام", tot)
                col_m2.metric("المهام المكتملة", dn)
                col_m3.metric("المهام المعلقة", pn)

                st.divider()
                st.dataframe(tasks_df, use_container_width=True)

        conn.close()

    # --- 4. Clients Management & Full Data ---
    elif choice == t["cs"]:
        st.title(f"📞 {t['cs']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        with st.expander(f"➕ {t['add_client']}"):
            with st.form("add_client_form"):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    c_name = st.text_input(t["client_name"])
                    c_phone = st.text_input(t["phone"])
                    c_nid = st.text_input(t["national_id"])
                with col_c2:
                    c_addr = st.text_input(t["address"])
                    c_photo = st.file_uploader("صورة العميل / الهوية", type=["jpg", "png", "jpeg"])
                
                pkgs = pd.read_sql_query("SELECT id, name, price, details, editor_tasks, social_tasks, web_tasks FROM packages", conn)
                pkg_options = {f"{row['name']} ({row['price']:,.0f} EGP)": (row['id'], row['price'], row['details'], row['name'], row['editor_tasks'], row['social_tasks'], row['web_tasks']) for _, row in pkgs.iterrows()} if not pkgs.empty else {}
                
                selected_pkg_str = st.selectbox(t["select_package"], list(pkg_options.keys()) if pkg_options else ["N/A"])
                c_notes = st.text_area(t["notes"])
                
                if st.form_submit_button(t["save"], type="primary"):
                    if c_name and pkg_options:
                        pkg_id, pkg_price, pkg_details, pkg_name, editor_t, social_t, web_t = pkg_options[selected_pkg_str]
                        
                        initial_tasks = {}
                        if pkg_details:
                            services = [s.strip() for s in pkg_details.replace("\n", ",").split(",") if s.strip()]
                            for service in services:
                                initial_tasks[service] = False
                        
                        current_date_str = datetime.now().strftime("%Y-%m-%d")
                        now_full_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        c_photo_path = save_uploaded_file(c_photo, prefix="client") if c_photo else ""

                        c.execute("""
                            INSERT INTO clients (client_name, phone, national_id, address, photo_path, package_id, notes, tasks_status, created_at) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (c_name, c_phone, c_nid, c_addr, c_photo_path, pkg_id, c_notes, json.dumps(initial_tasks, ensure_ascii=False), current_date_str))
                        
                        c.execute("INSERT INTO incomes (client_name, package_name, amount, added_by) VALUES (?, ?, ?, ?)",
                                  (c_name, pkg_name, pkg_price, st.session_state.user_info["name"]))
                        
                        # Auto Assignments
                        for task_item in parse_and_split_tasks(editor_t, "مونتاج"):
                            c.execute("INSERT INTO assigned_tasks (client_name, assigned_role, assigned_user_name, task_description, created_at) VALUES (?, ?, ?, ?, ?)",
                                      (c_name, "Editor", find_matching_employee("Editor", conn), task_item, now_full_str))

                        for task_item in parse_and_split_tasks(social_t, "سوشيال"):
                            c.execute("INSERT INTO assigned_tasks (client_name, assigned_role, assigned_user_name, task_description, created_at) VALUES (?, ?, ?, ?, ?)",
                                      (c_name, "Social Media Specialist", find_matching_employee("Social Media Specialist", conn), task_item, now_full_str))

                        for task_item in parse_and_split_tasks(web_t, "تصميم"):
                            c.execute("INSERT INTO assigned_tasks (client_name, assigned_role, assigned_user_name, task_description, created_at) VALUES (?, ?, ?, ?, ?)",
                                      (c_name, "Web Designer", find_matching_employee("Web Designer", conn), task_item, now_full_str))

                        conn.commit()
                        st.success(t["client_added"])
                        st.rerun()

        df_clients = pd.read_sql_query('''
            SELECT c.id, c.client_name, c.phone, c.national_id, c.address, p.name as package_name, p.price, COALESCE(p.duration_days, 30) as duration_days, c.created_at, c.notes 
            FROM clients c 
            LEFT JOIN packages p ON c.package_id = p.id
        ''', conn)
        
        st.subheader(f"📋 {t['clients_list']}")
        st.dataframe(df_clients, use_container_width=True)
        conn.close()

    # --- 5. Expenses Log & File Upload Engine ---
    elif choice == t["expenses"]:
        st.title(f"💸 {t['expenses']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        tab_log_exp, tab_upload_exp = st.tabs(["✍️ تسجيل مصروف يدوي", t["upload_exp_sheet"]])
        
        with tab_log_exp:
            with st.form("add_expense_form"):
                e_title = st.text_input(t["exp_title"])
                e_amount = st.number_input(t["amount"], min_value=0.0)
                e_cat = st.selectbox(t["category"], ["Operational", "Salaries", "Equipment", "Marketing", "Other"])
                
                if st.form_submit_button(t["log_exp_btn"], type="primary"):
                    if e_title and e_amount > 0:
                        c.execute("INSERT INTO expenses (title, amount, category, added_by) VALUES (?, ?, ?, ?)",
                                  (e_title, e_amount, e_cat, st.session_state.user_info["name"]))
                        conn.commit()
                        st.success(t["exp_saved"])
                        st.rerun()

        with tab_upload_exp:
            st.info("قم برفع شيت Excel أو CSV للمصروفات، ويجب أن يحتوي على الأعمدة: (Title, Amount, Category) أو (البيان, المبلغ, القسم)")
            uploaded_exp_file = st.file_uploader("اختر شيت المصروفات", type=["xlsx", "xls", "csv"])
            
            if uploaded_exp_file is not None:
                try:
                    if uploaded_exp_file.name.endswith('.csv'):
                        df_uploaded = pd.read_csv(uploaded_exp_file)
                    else:
                        df_uploaded = pd.read_excel(uploaded_exp_file)
                    
                    st.write("🔍 معاينة البيانات المرفوعة:")
                    st.dataframe(df_uploaded.head(), use_container_width=True)
                    
                    if st.button("تأكيد وحفظ بيانات الشيت في قاعدة البيانات 🚀", type="primary"):
                        count = 0
                        for _, r in df_uploaded.iterrows():
                            title = str(r.get('Title', r.get('البيان', r.get('بيان المصروف', 'مصروف غير معرف'))))
                            amount = float(r.get('Amount', r.get('المبلغ', 0.0)))
                            category = str(r.get('Category', r.get('القسم', 'Other')))
                            
                            if amount > 0:
                                c.execute("INSERT INTO expenses (title, amount, category, added_by) VALUES (?, ?, ?, ?)",
                                          (title, amount, category, st.session_state.user_info["name"]))
                                count += 1
                        conn.commit()
                        st.success(f"تم سحب واستيراد {count} مصروف من الشيت بنجاح! 🎉")
                        st.rerun()
                except Exception as ex:
                    st.error(f"حدث خطأ أثناء قراءة الشيت: {ex}")

        conn.close()

    # --- 6. Packages Management ---
    elif choice == t["packages"]:
        st.title(f"📦 {t['packages']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        if role == "Owner":
            with st.expander(f"➕ {t['add_pkg']}"):
                with st.form("add_package_form"):
                    p_name = st.text_input(t["pkg_name"])
                    p_price = st.number_input(t["price"], min_value=0.0)
                    p_duration = st.number_input(t["pkg_duration"], min_value=1, value=30, step=1)
                    p_details = st.text_area(t["details"])
                    p_editor_tasks = st.text_area(t["editor_tasks"])
                    p_social_tasks = st.text_area(t["social_tasks"])
                    p_web_tasks = st.text_area(t["web_tasks"])
                    
                    if st.form_submit_button(t["save"], type="primary"):
                        c.execute("INSERT INTO packages (name, price, details, duration_days, editor_tasks, social_tasks, web_tasks) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                  (p_name, p_price, p_details, int(p_duration), p_editor_tasks, p_social_tasks, p_web_tasks))
                        conn.commit()
                        st.success("تم إضافة الباقة بنجاح!")
                        st.rerun()
        
        df_pkgs = pd.read_sql_query("SELECT * FROM packages", conn)
        st.dataframe(df_pkgs, use_container_width=True)
        conn.close()

    # --- 7. CCTV Surveillance Tab ---
    elif choice == t["cameras"]:
        st.title(f"📹 {t['cameras']}")
        conn = get_db_connection()
        c = conn.cursor()

        if role in ["Owner", "Manager"]:
            with st.expander("➕ إضافة كاميرا مراقبة جديدة"):
                with st.form("add_cam_form"):
                    cam_name = st.text_input("اسم الكاميرا / المكان (مثال: كاميرا المونتاج الرئيسية)")
                    stream_url = st.text_input("رابط البث (RTSP / IP Camera / Stream URL / Embed Link)")
                    location = st.text_input("الموقع", value="المقر الرئيسي")
                    
                    if st.form_submit_button("إضافة الكاميرا 🎥", type="primary"):
                        if cam_name and stream_url:
                            c.execute("INSERT INTO cameras (cam_name, stream_url, location) VALUES (?, ?, ?)",
                                      (cam_name, stream_url, location))
                            conn.commit()
                            st.success("تمت إضافة الكاميرا بنجاح!")
                            st.rerun()

        cams = c.execute("SELECT * FROM cameras").fetchall()
        if not cams:
            st.info("لا توجد كاميرات مراقبة مضافة حالياً. يمكنك إضافة كاميرات جديدة من الأعلى.")
        else:
            cols = st.columns(2)
            for idx, cam in enumerate(cams):
                cam_id, c_name, c_url, c_loc = cam
                with cols[idx % 2]:
                    st.markdown(f"### 📹 {c_name} ({c_loc})")
                    if "http" in c_url or "https" in c_url:
                        st.components.v1.iframe(c_url, height=350)
                    else:
                        st.warning(f"رابط كاميرا RTSP/IP: `{c_url}` (يتطلب مشغل مباشر أو كود Stream مفعل)")

        conn.close()

    # --- 8. Fingerprint Attendance System (Linked by Employee ID) ---
    elif choice == t["attendance"]:
        st.title(f"🖐️ {t['attendance']}")
        conn = get_db_connection()
        c = conn.cursor()

        st.info("💡 يتم ربط شيت البصمة تلقائياً برقم الـ ID الخاص بالموظف المسجل في النظام.")

        if role in ["Owner", "Manager"]:
            with st.expander("📥 رفع شيت جهاز البصمة الشهري (Excel / CSV)"):
                uploaded_att_file = st.file_uploader("اختر شيت الحضور والبصمة", type=["xlsx", "xls", "csv"], key="att_file")
                if uploaded_att_file:
                    try:
                        df_att = pd.read_csv(uploaded_att_file) if uploaded_att_file.name.endswith('.csv') else pd.read_excel(uploaded_att_file)
                        st.dataframe(df_att.head(), use_container_width=True)

                        if st.button("معالجة وربط الشيت بالـ ID 🚀", type="primary"):
                            matched = 0
                            for _, r in df_att.iterrows():
                                emp_id = int(r.get('Employee ID', r.get('ID', r.get('كود الموظف', 0))))
                                att_date = str(r.get('Date', r.get('التاريخ', datetime.now().strftime('%Y-%m-%d'))))
                                check_in = str(r.get('Check In', r.get('دخول', '-')))
                                check_out = str(r.get('Check Out', r.get('خروج', '-')))
                                
                                # Verify Emp ID
                                emp_match = c.execute("SELECT name FROM users WHERE id = ?", (emp_id,)).fetchone()
                                emp_name = emp_match[0] if emp_match else "غير معروف"

                                if emp_id > 0:
                                    c.execute("INSERT INTO attendance (emp_id, emp_name, date, check_in, check_out) VALUES (?, ?, ?, ?, ?)",
                                              (emp_id, emp_name, att_date, check_in, check_out))
                                    matched += 1
                            conn.commit()
                            st.success(f"تم ربط وقراءة {matched} سجلاً من الشيت بنجاح!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"خطأ في الشيت: {e}")

        st.subheader("📋 سجل الحضور والبصمة المسجل")
        df_att_db = pd.read_sql_query("SELECT * FROM attendance", conn)
        st.dataframe(df_att_db, use_container_width=True)
        conn.close()

    # --- 9. Full Financial Audit Sheet (Owner Only) ---
    elif choice == t["audit"] and role == "Owner":
        st.title(f"📊 {t['audit']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            selected_year = st.number_input("السنة المالية", min_value=2020, max_value=2030, value=datetime.now().year)
        with col_m2:
            selected_month = st.selectbox("الشهر المالي", options=list(range(1, 13)), index=datetime.now().month - 1)
        
        _, last_day = calendar.monthrange(selected_year, selected_month)
        start_date_str = f"{selected_year}-{selected_month:02d}-01 00:00:00"
        end_date_str = f"{selected_year}-{selected_month:02d}-{last_day:02d} 23:59:59"
        
        st.info(f"📅 نطاق الشيت للمصروفات والإيرادات: من **1-{selected_month:02d}-{selected_year}** إلى **{last_day}-{selected_month:02d}-{selected_year}**")

        df_exp = pd.read_sql_query("SELECT id, title, amount, category, added_by, date FROM expenses WHERE date >= ? AND date <= ?", conn, params=(start_date_str, end_date_str))
        df_inc = pd.read_sql_query("SELECT id, client_name, package_name, amount, added_by, date FROM incomes WHERE date >= ? AND date <= ?", conn, params=(start_date_str, end_date_str))
        
        total_outcomes = df_exp['amount'].sum() if not df_exp.empty else 0.0
        total_incomes = df_inc['amount'].sum() if not df_inc.empty else 0.0
        net_profit = total_incomes - total_outcomes
        
        col1, col2, col3 = st.columns(3)
        col1.metric(t["total_inc"], f"{total_incomes:,.2f} EGP")
        col2.metric(t["total_exp"], f"{total_outcomes:,.2f} EGP")
        col3.metric(t["net_profit"], f"{net_profit:,.2f} EGP", delta=f"{net_profit:,.2f} EGP")
        
        st.divider()
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_summary = pd.DataFrame({
                'البيان': ['إجمالي الإيرادات', 'إجمالي المصروفات', 'صافي الأرباح'],
                'المبلغ (EGP)': [total_incomes, total_outcomes, net_profit]
            })
            df_summary.to_excel(writer, index=False, sheet_name='Summary')
            df_inc.to_excel(writer, index=False, sheet_name='Incomes')
            df_exp.to_excel(writer, index=False, sheet_name='Expenses')
            
        excel_data = output.getvalue()
        
        st.download_button(
            label=t["export_excel"],
            data=excel_data,
            file_name=f"focal_craft_monthly_audit_{selected_year}_{selected_month}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        conn.close()
