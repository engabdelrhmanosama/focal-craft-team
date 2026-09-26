import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import base64
import json
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO

# ==========================================
# 1. Page Config & Logo Setup
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

logo_base64 = get_image_base64(logo_path)

# Custom Styling Injection for Professional Dashboard UI
def inject_custom_css():
    st.markdown("""
        <style>
        /* Import Modern Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Cairo', 'Inter', sans-serif;
        }

        /* Card Container Styling */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(30, 41, 59, 0.6) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 12px !important;
            padding: 16px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.25);
        }

        /* Metric Cards Styling */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9)) !important;
            padding: 16px !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }

        /* Button Styling */
        .stButton>button {
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }

        /* Primary Action Buttons */
        .stButton>button[kind="primary"] {
            background: linear-gradient(135deg, #ef4444, #dc2626) !important;
            border: none !important;
            color: white !important;
        }

        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# ==========================================
# 2. Database Connection & Schema (SQLite)
# ==========================================
DB_FILE = "/tmp/focal_craft.db"

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    
    # Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT NOT NULL,
            salary REAL DEFAULT 0.0
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
            social_tasks TEXT DEFAULT ''
        )
    ''')
    
    # Clients Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            phone TEXT,
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
    
    # Auto-Migrations
    c.execute("PRAGMA table_info(users)")
    user_cols = [col[1] for col in c.fetchall()]
    if 'salary' not in user_cols:
        try:
            c.execute("ALTER TABLE users ADD COLUMN salary REAL DEFAULT 0.0")
        except Exception:
            pass

    c.execute("PRAGMA table_info(packages)")
    pkg_cols = [col[1] for col in c.fetchall()]
    if 'duration_days' not in pkg_cols:
        try:
            c.execute("ALTER TABLE packages ADD COLUMN duration_days INTEGER DEFAULT 30")
        except Exception:
            pass
    if 'editor_tasks' not in pkg_cols:
        try:
            c.execute("ALTER TABLE packages ADD COLUMN editor_tasks TEXT DEFAULT ''")
        except Exception:
            pass
    if 'social_tasks' not in pkg_cols:
        try:
            c.execute("ALTER TABLE packages ADD COLUMN social_tasks TEXT DEFAULT ''")
        except Exception:
            pass

    c.execute("PRAGMA table_info(clients)")
    client_cols = [col[1] for col in c.fetchall()]
    if 'tasks_status' not in client_cols:
        try:
            c.execute("ALTER TABLE clients ADD COLUMN tasks_status TEXT DEFAULT '{}'")
        except Exception:
            pass
    if 'created_at' not in client_cols:
        try:
            c.execute("ALTER TABLE clients ADD COLUMN created_at TEXT")
        except Exception:
            pass

    # Default Owner User Configuration
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

# ==========================================
# 3. Session State & Multi-Language Dictionary
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "lang" not in st.session_state:
    st.session_state.lang = "AR"
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

if st.session_state.theme == "Light":
    st.markdown("""
        <style>
        .stApp {
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }
        .stSidebar {
            background-color: #f1f5f9 !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
        }
        div[data-testid="stMetric"] {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

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
        "my_tasks": "My Assigned Tasks",
        "cs": "Clients & Services Tracking",
        "expenses": "Log Expense",
        "packages": "Packages Management",
        "employees": "Employee Hub & Tasks",
        "audit": "Financial Audit & Sheet (Owner Only)",
        "logout": "Logout",
        "status": "System Status",
        "active": "Active 🟢",
        "add_pkg": "Add New Package",
        "pkg_name": "Package Name",
        "price": "Price",
        "pkg_duration": "Package Duration (Days)",
        "details": "General Package Details",
        "editor_tasks": "Editor Tasks (e.g. Edit 3 videos, Design 1 thumbnail)",
        "social_tasks": "Social Media Tasks (e.g. Write 3 posts, Schedule publishing)",
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
        "select_package": "Select Package",
        "notes": "Notes",
        "client_added": "Client added, income logged & employee tasks generated automatically!",
        "clients_list": "Subscribed Clients List",
        "track_services": "Track Package Services & Tasks",
        "select_client_track": "Select client to view or update services:",
        "save_tasks": "Save Service Status 💾",
        "tasks_saved": "Client service status updated successfully!",
        "no_packages_err": "Please contact owner to add packages first!",
        "exp_title": "Expense Title / Description",
        "amount": "Amount",
        "category": "Category",
        "log_exp_btn": "Log Expense",
        "exp_saved": "Expense logged successfully!",
        "exp_err": "Please enter valid title and amount.",
        "delete_pkg": "Delete Package",
        "pkg_deleted": "Package deleted successfully!",
        "save_user_changes": "Save Changes 💾",
        "user_updated": "User details updated successfully!",
        "user_deleted": "User deleted successfully!",
        "total_exp": "Total Expenses (Outcomes)",
        "total_inc": "Total Revenue (Incomes)",
        "net_profit": "Net Profit",
        "export_excel": "📥 Export Financial Sheet (Excel)",
        "delete_exp": "Delete Expense",
        "exp_deleted": "Expense deleted successfully!",
        "no_clients": "No clients registered yet.",
        "no_pkg_assigned": "Client is not assigned to any package.",
        "completion_rate": "Service Completion Rate:",
        "delete_client": "Delete Client (Owner Only)",
        "client_deleted": "Client deleted successfully!",
        "emp_team_head": "📋 Current Team Members",
        "no_employees_msg": "No employees found matching the search.",
        "job_title": "Job Title",
        "salary_txt": "Monthly Salary",
        "actions_btn": "⚙️ Options / Edit / Delete",
        "edit_emp_modal": "Settings for account:",
        "new_pass_optional": "New Password (leave empty to keep current)",
        "del_emp_permanently": "🗑️ Delete Employee Permanently",
        "cannot_del_self": "You cannot delete your active logged-in account.",
        "task_overview": "📈 Employee Task & Timeline Tracking",
        "no_tasks_msg": "No tasks assigned to employees yet.",
        "total_tasks": "Total Assigned Tasks",
        "completed_tasks": "Completed Tasks ✅",
        "pending_tasks": "Pending Tasks ⏳",
        "tasks_for_role": "📌 Tasks assigned to role:",
        "col_task_id": "Task ID",
        "col_client": "Client Name",
        "col_desc": "Task Description",
        "col_status": "Status",
        "col_created": "Date Created",
        "col_completed": "Completion Date & Time ⏱️",
        "tab_emp_mgmt": "👤 Employee Management",
        "tab_emp_tasks": "📊 Task Completion & Timeline Tracking",
        "search_emp_placeholder": "🔍 Search employee by Name, ID, Username, or Role...",
        "emp_id_label": "Employee ID (Custom)",
        "id_exists_err": "This ID is already used by another employee!"
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
        "my_tasks": "مهامي والشغل المطلوب",
        "cs": "إدارة العملاء ومتابعة الخدمات",
        "expenses": "تسجيل مصروف",
        "packages": "إدارة الباقات",
        "employees": "الموظفين والمرتبات ومتابعة المهام",
        "audit": "شيت الحسابات والتدقيق المالي (المالك فقط)",
        "logout": "تسجيل الخروج",
        "status": "حالة النظام",
        "active": "نشط 🟢",
        "add_pkg": "إضافة باقة جديدة",
        "pkg_name": "اسم الباقة",
        "price": "السعر",
        "pkg_duration": "مدة الباقة (بالأيام)",
        "details": "تفاصيل الباقة العامة",
        "editor_tasks": "مهام المونتير/الإيديتور (مثل: مونتاج 3 فيديوهات وصورة)",
        "social_tasks": "مهام مسؤول السوشيال ميديا (مثل: كتابة 3 بوستات ونشرها)",
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
        "select_package": "اختر الباقة",
        "notes": "ملاحظات",
        "client_added": "تمت إضافة العميل، إيراد الباقة، وتحويل المهام للموظفين تلقائياً!",
        "clients_list": "قائمة العملاء المشتركين",
        "track_services": "متابعة تنفيذ خدمات الباقة للعملاء",
        "select_client_track": "اختر العميل لمتابعة أو تقديم الخدمات الخاصة به:",
        "save_tasks": "حفظ تحديثات الخدمات 💾",
        "tasks_saved": "تم حفظ حالة الخدمات للعميل بنجاح!",
        "no_packages_err": "يرجى التواصل مع المالك لإضافة باقات أولاً!",
        "exp_title": "بيان المصروف (السبب/الوصف)",
        "amount": "المبلغ",
        "category": "القسم",
        "log_exp_btn": "تسجيل المصروف",
        "exp_saved": "تم تسجيل المصروف بنجاح!",
        "exp_err": "يرجى إدخال المبلغ والبيان بشكل صحيح.",
        "delete_pkg": "حذف باقة",
        "pkg_deleted": "تم حذف الباقة بنجاح!",
        "save_user_changes": "حفظ التعديلات 💾",
        "user_updated": "تم تحديث بيانات الموظف والمرتب بنجاح!",
        "user_deleted": "تم حذف الموظف بنجاح!",
        "total_exp": "إجمالي المصروفات (الخارج)",
        "total_inc": "إجمالي الإيرادات (الداخل)",
        "net_profit": "صافي أرباح الشركة",
        "export_excel": "📥 سحب الشيت المالي المكتمل (Excel)",
        "delete_exp": "مسح مصروف محدد",
        "exp_deleted": "تم مسح المصروف بنجاح!",
        "no_clients": "لا يوجد عملاء مسجلين حالياً.",
        "no_pkg_assigned": "العميل غير مشترك في باقة حالياً.",
        "completion_rate": "نسبة إنجاز الخدمات:",
        "delete_client": "حذف عميل (المالك فقط)",
        "client_deleted": "تم حذف العميل بنجاح!",
        "emp_team_head": "📋 فريق العمل الحالي",
        "no_employees_msg": "لم يتم العثور على موظفين مطابقين للبحث.",
        "job_title": "الوظيفة",
        "salary_txt": "المرتب الشهري",
        "actions_btn": "⚙️ خيارات / تعديل / حذف",
        "edit_emp_modal": "إعدادات حساب:",
        "new_pass_optional": "كلمة سر جديدة (اتركها فارغة بدون تغيير)",
        "del_emp_permanently": "🗑️ حذف الموظف نهائياً",
        "cannot_del_self": "لا يمكنك حذف حسابك الحالي الذي تستخدمه الآن.",
        "task_overview": "📈 لوحة متابعة إنجاز الموظفين وتوقيت الانتهاء",
        "no_tasks_msg": "لا توجد مهام مسجلة ومحولة للموظفين حتى الآن.",
        "total_tasks": "إجمالي المهام المحولة",
        "completed_tasks": "المهام المكتملة ✅",
        "pending_tasks": "المهام قيد التنفيذ ⏳",
        "tasks_for_role": "📌 المهام الموجهة لوظيفة:",
        "col_task_id": "رقم المهمة",
        "col_client": "العميل",
        "col_desc": "تفاصيل المهمة المطلوب تنفيذها",
        "col_status": "حالة المهمة",
        "col_created": "تاريخ الإنشاء",
        "col_completed": "تاريخ وتوقيت الإنجاز ⏱️",
        "tab_emp_mgmt": "👤 إدارة الموظفين والمرتبات",
        "tab_emp_tasks": "📊 متابعة إنجاز مهام الموظفين والتوقيت",
        "search_emp_placeholder": "🔍 ابحث عن موظف بالاسم، الرقم التعريفي (ID)، اليوزر، أو الوظيفة...",
        "emp_id_label": "الرقم التعريفي (ID مخصص)",
        "id_exists_err": "هذا الرقم التعريفي مستخدم بالفعل لموظف آخر!"
    }
}

t = translations[st.session_state.lang]

# ==========================================
# 4. Login Interface
# ==========================================
if not st.session_state.logged_in:
    if st.session_state.theme == "Dark":
        bg_style = f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(15, 23, 42, 0.9), rgba(15, 23, 42, 0.9)), 
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
        st.markdown(f"<h2 style='text-align: center; font-weight: 800;'>{t['title']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #94a3b8;'>{t['subtitle']}</p>", unsafe_allow_html=True)
        
        col_lang, col_theme = st.columns(2)
        with col_lang:
            selected_lang = st.radio("🌐 Language / اللغة", ["العربية", "English"], 
                                     index=0 if st.session_state.lang == "AR" else 1, horizontal=True)
            st.session_state.lang = "AR" if selected_lang == "العربية" else "EN"
            t = translations[st.session_state.lang]
        with col_theme:
            theme_choice = st.radio("☀️ Theme / المظهر", ["Dark", "Light"], horizontal=True)
            st.session_state.theme = theme_choice

        with st.form("login_form"):
            username = st.text_input(t["username"])
            password = st.text_input(t["password"], type="password")
            submit = st.form_submit_button(t["login_btn"], use_container_width=True, type="primary")
            
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
# 5. Main Dashboard
# ==========================================
else:
    with st.sidebar:
        if logo_img:
            st.image(logo_img, use_container_width=True)
        st.markdown(f"<h3 style='margin-bottom:0;'>{t['title']}</h3>", unsafe_allow_html=True)
        st.caption(f"✨ {t['subtitle']}")
        st.write(f"{t['welcome']}: **{st.session_state.user_info['name']}**")
        st.caption(f"{t['role']}: `{st.session_state.user_info['role']}`")
        
        lang_choice = st.radio("🌐 Language / اللغة", ["العربية", "English"], 
                               index=0 if st.session_state.lang == "AR" else 1, horizontal=True)
        st.session_state.lang = "AR" if lang_choice == "العربية" else "EN"
        t = translations[st.session_state.lang]
        
        theme_toggle = st.radio("☀️ Theme / المظهر", ["Dark 🌙", "Light ☀️"], 
                                index=0 if st.session_state.theme == "Dark" else 1, horizontal=True)
        st.session_state.theme = "Dark" if "Dark" in theme_toggle else "Light"
        
        st.divider()
        
        role = st.session_state.user_info["role"]
        
        menu_options = [t["home"], t["my_tasks"]]
        
        if role in ["Owner", "Manager"]:
            menu_options.append(t["employees"])
            
        menu_options.extend([t["cs"], t["expenses"], t["packages"]])
        
        if role == "Owner":
            menu_options.append(t["audit"])
            
        choice = st.radio(t["nav"], menu_options)
        
        st.divider()
        if st.button(t["logout"], use_container_width=True, type="primary"):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()

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
            tasks_df = pd.read_sql_query("SELECT * FROM assigned_tasks WHERE assigned_role = ?", conn, params=(role,))
        else:
            tasks_df = pd.read_sql_query("SELECT * FROM assigned_tasks", conn)

        pending_tasks = tasks_df[tasks_df["status"].isin(["Pending", "قيد التنفيذ"])] if not tasks_df.empty else pd.DataFrame()
        completed_tasks = tasks_df[tasks_df["status"].isin(["Completed ✅", "مكتمل ✅"])] if not tasks_df.empty else pd.DataFrame()

        tab1, tab2 = st.tabs(["⏳ Pending Tasks" if st.session_state.lang == "EN" else "⏳ مهام قيد التنفيذ", 
                              "✅ Completed Tasks" if st.session_state.lang == "EN" else "✅ مهام تم إنجازها"])

        with tab1:
            if pending_tasks.empty:
                st.info("No pending tasks assigned right now! 🎉" if st.session_state.lang == "EN" else "لا توجد مهام معلقة مطلوب تنفيذها حالياً! 🎉")
            else:
                for idx, row in pending_tasks.iterrows():
                    with st.expander(f"📌 Client: {row['client_name']} - {row['task_description']}"):
                        st.write(f"**Task:** {row['task_description']}")
                        st.write(f"**Target Role:** {row['assigned_role']}")
                        st.write(f"**Created At:** {row['created_at']}")
                        
                        done_label = "Mark as Done ✅" if st.session_state.lang == "EN" else "تحديد كـ مكتمل ✅"
                        if st.button(done_label, key=f"task_done_{row['id']}", type="primary"):
                            c.execute("UPDATE assigned_tasks SET status = 'Completed ✅', completed_at = ? WHERE id = ?",
                                      (datetime.now().strftime("%Y-%m-%d %H:%M"), row['id']))
                            conn.commit()
                            st.success("Task status updated successfully! 🚀" if st.session_state.lang == "EN" else "تم تحديث حالة التاسك وإنجازه بنجاح! 🚀")
                            st.rerun()

        with tab2:
            if completed_tasks.empty:
                st.caption("No completed tasks yet." if st.session_state.lang == "EN" else "لم يتم إنجاز مهام بعد.")
            else:
                st.dataframe(completed_tasks[["client_name", "assigned_role", "task_description", "completed_at"]], use_container_width=True)
                
        conn.close()

    # --- 3. Simplified Modern Employee Hub with Custom ID & Search ---
    elif choice == t.get("employees") and role in ["Owner", "Manager"]:
        st.title(f"👥 {t['employees']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        tab_emp_mgmt, tab_emp_tasks = st.tabs([
            t["tab_emp_mgmt"], 
            t["tab_emp_tasks"]
        ])

        # --- Tab A: Employee Management Cards & Custom ID ---
        with tab_emp_mgmt:
            col_head1, col_head2 = st.columns([3, 1])
            with col_head1:
                st.subheader(t["emp_team_head"])
            with col_head2:
                with st.popover(t["add_emp"], use_container_width=True):
                    st.markdown(f"### {t['add_emp_modal_title']}")
                    with st.form("quick_add_emp"):
                        u_custom_id = st.number_input(f"{t['emp_id_label']} (اختياري/أتركه فارغاً تلقائي)", min_value=1, step=1, value=None)
                        u_fullname = st.text_input(t["fullname"])
                        u_username = st.text_input(t["username"])
                        u_password = st.text_input(t["password"], type="password")
                        u_role_preset = st.selectbox(t["role"], ["Owner", "Manager", "Editor", "Social Media Specialist", "Other / Custom"])
                        
                        if "Custom" in u_role_preset or "أخرى" in u_role_preset:
                            u_role_custom = st.text_input("Custom Role Title / الوظيفة المخصصة:")
                            final_role = u_role_custom.strip() if u_role_custom.strip() != "" else "Employee"
                        else:
                            final_role = u_role_preset
                            
                        u_salary = st.number_input(f"{t['salary_txt']} (EGP)", min_value=0.0, step=500.0)

                        if st.form_submit_button(f"{t['save']} 🚀", use_container_width=True, type="primary"):
                            if u_fullname and u_username and u_password:
                                try:
                                    if u_custom_id:
                                        c.execute("INSERT INTO users (id, username, password, role, name, salary) VALUES (?, ?, ?, ?, ?, ?)",
                                                  (int(u_custom_id), u_username, hash_pass(u_password), final_role, u_fullname, u_salary))
                                    else:
                                        c.execute("INSERT INTO users (username, password, role, name, salary) VALUES (?, ?, ?, ?, ?)",
                                                  (u_username, hash_pass(u_password), final_role, u_fullname, u_salary))
                                    conn.commit()
                                    st.success(t["emp_added"])
                                    st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error(t["user_exists"])
                            else:
                                st.error("Please fill in all required fields." if st.session_state.lang == "EN" else "يرجى ملء جميع البيانات الأساسية.")

            # Search Bar Interface
            search_query = st.text_input("", placeholder=t["search_emp_placeholder"])

            # Query All Users
            all_users = c.execute("SELECT id, name, username, role, salary FROM users").fetchall()

            # Filter Users Based on Search Input
            if search_query.strip() != "":
                q = search_query.strip().lower()
                filtered_users = [
                    u for u in all_users 
                    if q in str(u[0]).lower()             # ID search
                    or q in u[1].lower()                  # Name search
                    or q in u[2].lower()                  # Username search
                    or q in u[3].lower()                  # Role search
                ]
            else:
                filtered_users = all_users

            st.divider()

            if not filtered_users:
                st.info(t["no_employees_msg"])
            else:
                cols_per_row = 2
                for i in range(0, len(filtered_users), cols_per_row):
                    row_users = filtered_users[i:i+cols_per_row]
                    cols = st.columns(cols_per_row)
                    
                    for idx, user_data in enumerate(row_users):
                        u_id, u_name, u_uname, u_role, u_sal = user_data
                        
                        with cols[idx]:
                            with st.container(border=True):
                                col_card_title, col_card_id = st.columns([3, 1])
                                with col_card_title:
                                    st.markdown(f"### 👤 {u_name}")
                                with col_card_id:
                                    st.markdown(f"**`ID: #{u_id}`**")
                                    
                                st.markdown(f"💼 **{t['job_title']}:** `{u_role}`")
                                st.markdown(f"💰 **{t['salary_txt']}:** `{u_sal:,.2f} EGP`")
                                st.caption(f"🔑 {t['username']}: {u_uname} | 🆔 ID: #{u_id}")

                                # Action Popover for Editing/Deleting
                                with st.popover(t["actions_btn"], use_container_width=True):
                                    st.markdown(f"#### {t['edit_emp_modal']} {u_name}")
                                    
                                    with st.form(f"edit_form_{u_id}"):
                                        e_id = st.number_input(t["emp_id_label"], value=int(u_id), step=1, min_value=1)
                                        e_fullname = st.text_input(t["fullname"], value=u_name)
                                        e_username = st.text_input(t["username"], value=u_uname)
                                        e_role = st.text_input(t["job_title"], value=u_role)
                                        e_salary = st.number_input(f"{t['salary_txt']} (EGP)", value=float(u_sal if u_sal else 0.0), step=500.0)
                                        e_password = st.text_input(t["new_pass_optional"], type="password")

                                        if st.form_submit_button(t["save_user_changes"], use_container_width=True, type="primary"):
                                            try:
                                                if e_password.strip() != "":
                                                    c.execute("UPDATE users SET id = ?, username = ?, name = ?, role = ?, salary = ?, password = ? WHERE id = ?", 
                                                              (e_id, e_username, e_fullname, e_role, e_salary, hash_pass(e_password), u_id))
                                                else:
                                                    c.execute("UPDATE users SET id = ?, username = ?, name = ?, role = ?, salary = ? WHERE id = ?", 
                                                              (e_id, e_username, e_fullname, e_role, e_salary, u_id))
                                                conn.commit()
                                                st.success(t["user_updated"])
                                                st.rerun()
                                            except sqlite3.IntegrityError:
                                                st.error(t["user_exists"])

                                    st.divider()
                                    if u_uname != st.session_state.user_info["username"]:
                                        if st.button(t["del_emp_permanently"], key=f"del_{u_id}", type="primary", use_container_width=True):
                                            c.execute("DELETE FROM users WHERE id = ?", (u_id,))
                                            conn.commit()
                                            st.success(t["user_deleted"])
                                            st.rerun()
                                    else:
                                        st.caption(t["cannot_del_self"])

        # --- Tab B: Tasks & Timeline Dashboard ---
        with tab_emp_tasks:
            st.subheader(t["task_overview"])
            
            tasks_df = pd.read_sql_query("SELECT * FROM assigned_tasks", conn)
            
            if tasks_df.empty:
                st.info(t["no_tasks_msg"])
            else:
                col_m1, col_m2, col_m3 = st.columns(3)
                tot = len(tasks_df)
                dn = len(tasks_df[tasks_df["status"].isin(["Completed ✅", "مكتمل ✅"])])
                pn = tot - dn

                col_m1.metric(t["total_tasks"], tot)
                col_m2.metric(t["completed_tasks"], dn)
                col_m3.metric(t["pending_tasks"], pn)

                st.divider()
                
                roles_in_tasks = tasks_df["assigned_role"].unique()
                for r in roles_in_tasks:
                    with st.expander(f"{t['tasks_for_role']} **{r}**", expanded=True):
                        sub_df = tasks_df[tasks_df["assigned_role"] == r]
                        st.dataframe(
                            sub_df[["id", "client_name", "task_description", "status", "created_at", "completed_at"]].rename(
                                columns={
                                    "id": t["col_task_id"],
                                    "client_name": t["col_client"],
                                    "task_description": t["col_desc"],
                                    "status": t["col_status"],
                                    "created_at": t["col_created"],
                                    "completed_at": t["col_completed"]
                                }
                            ), 
                            use_container_width=True
                        )

        conn.close()

    # --- 4. Clients & Services Checklist Tracking ---
    elif choice == t["cs"]:
        st.title(f"📞 {t['cs']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        # Add Client Form
        with st.expander(f"➕ {t['add_client']}"):
            with st.form("add_client_form"):
                c_name = st.text_input(t["client_name"])
                c_phone = st.text_input(t["phone"])
                
                pkgs = pd.read_sql_query("SELECT id, name, price, details, editor_tasks, social_tasks FROM packages", conn)
                pkg_options = {f"{row['name']} ({row['price']:,.0f} EGP)": (row['id'], row['price'], row['details'], row['name'], row['editor_tasks'], row['social_tasks']) for _, row in pkgs.iterrows()} if not pkgs.empty else {}
                
                selected_pkg_str = st.selectbox(t["select_package"], list(pkg_options.keys()) if pkg_options else ["N/A"])
                c_notes = st.text_area(t["notes"])
                
                if st.form_submit_button(t["save"], type="primary"):
                    if c_name and pkg_options:
                        pkg_id, pkg_price, pkg_details, pkg_name, editor_t, social_t = pkg_options[selected_pkg_str]
                        
                        initial_tasks = {}
                        if pkg_details:
                            services = [s.strip() for s in pkg_details.replace("\n", ",").split(",") if s.strip()]
                            for service in services:
                                initial_tasks[service] = False
                        
                        current_date_str = datetime.now().strftime("%Y-%m-%d")
                        now_full_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        c.execute("INSERT INTO clients (client_name, phone, package_id, notes, tasks_status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                  (c_name, c_phone, pkg_id, c_notes, json.dumps(initial_tasks, ensure_ascii=False), current_date_str))
                        
                        c.execute("INSERT INTO incomes (client_name, package_name, amount, added_by) VALUES (?, ?, ?, ?)",
                                  (c_name, pkg_name, pkg_price, st.session_state.user_info["name"]))
                        
                        if editor_t and editor_t.strip() != "":
                            c.execute("INSERT INTO assigned_tasks (client_name, assigned_role, task_description, created_at) VALUES (?, ?, ?, ?)",
                                      (c_name, "Editor", editor_t, now_full_str))
                        if social_t and social_t.strip() != "":
                            c.execute("INSERT INTO assigned_tasks (client_name, assigned_role, task_description, created_at) VALUES (?, ?, ?, ?)",
                                      (c_name, "Social Media Specialist", social_t, now_full_str))
                        
                        conn.commit()
                        st.success(t["client_added"])
                        st.rerun()
                    elif not pkg_options:
                        st.error(t["no_packages_err"])

        # Display Clients DataFrame
        df_clients = pd.read_sql_query('''
            SELECT c.id, c.client_name, c.phone, p.name as package_name, p.price, COALESCE(p.duration_days, 30) as duration_days, c.created_at, c.notes 
            FROM clients c 
            LEFT JOIN packages p ON c.package_id = p.id
        ''', conn)
        
        if not df_clients.empty:
            today = datetime.now().date()
            days_left_list = []
            status_list = []
            
            for idx, row in df_clients.iterrows():
                created_str = row['created_at']
                pkg_days = int(row['duration_days']) if pd.notnull(row['duration_days']) else 30
                
                if pd.notnull(created_str) and created_str != "":
                    try:
                        start_date = datetime.strptime(created_str, "%Y-%m-%d").date()
                        end_date = start_date + timedelta(days=pkg_days)
                        remaining = (end_date - today).days
                        if remaining > 0:
                            days_left_list.append(f"{remaining} Days" if st.session_state.lang == "EN" else f"{remaining} يوم")
                            status_list.append("Active 🟢" if st.session_state.lang == "EN" else "نشط 🟢")
                        else:
                            days_left_list.append("0 Days" if st.session_state.lang == "EN" else "0 يوم")
                            status_list.append("Expired 🔴" if st.session_state.lang == "EN" else "منتهي 🔴")
                    except Exception:
                        days_left_list.append("N/A")
                        status_list.append("Active 🟢" if st.session_state.lang == "EN" else "نشط 🟢")
                else:
                    days_left_list.append("N/A")
                    status_list.append("Active 🟢" if st.session_state.lang == "EN" else "نشط 🟢")
            
            df_clients['Days Remaining' if st.session_state.lang == "EN" else 'المتبقي من الباقة'] = days_left_list
            df_clients['Subscription Status' if st.session_state.lang == "EN" else 'حالة الاشتراك'] = status_list

        st.subheader(f"📋 {t['clients_list']}")
        st.dataframe(df_clients, use_container_width=True)
        
        if role == "Owner" and not df_clients.empty:
            st.divider()
            st.subheader(f"🗑️ {t['delete_client']}")
            client_options = {f"{row['id']} - {row['client_name']}": row['id'] for _, row in df_clients.iterrows()}
            selected_client_del = st.selectbox("Select Client to Delete:" if st.session_state.lang == "EN" else "اختر العميل المراد حذفه نهائياً:", list(client_options.keys()))
            
            if st.button("Delete Selected Client ❌" if st.session_state.lang == "EN" else "حذف العميل المحدد ❌", type="primary"):
                client_id_to_del = client_options[selected_client_del]
                c.execute("DELETE FROM clients WHERE id = ?", (client_id_to_del,))
                conn.commit()
                st.success(t["client_deleted"])
                st.rerun()

        # Services Tracking Checklist Section
        st.divider()
        st.subheader(f"☑️ {t['track_services']}")
        
        c.execute('''
            SELECT c.id, c.client_name, p.name, c.tasks_status, p.details 
            FROM clients c 
            LEFT JOIN packages p ON c.package_id = p.id
        ''')
        clients_data = c.fetchall()
        
        if clients_data:
            client_names = [f"{row[0]} - {row[1]} ({row[2]})" for row in clients_data]
            selected_client_str = st.selectbox(t["select_client_track"], client_names)
            
            selected_id = int(selected_client_str.split(" - ")[0])
            
            c.execute("SELECT client_name, tasks_status, package_id FROM clients WHERE id = ?", (selected_id,))
            cl_info = c.fetchone()
            client_name, tasks_json, pkg_id = cl_info[0], cl_info[1], cl_info[2]
            
            c.execute("SELECT name, details FROM packages WHERE id = ?", (pkg_id,))
            pkg_info = c.fetchone()
            
            if pkg_info:
                st.markdown(f"#### Client: **{client_name}** | Package: **{pkg_info[0]}**")
                
                try:
                    tasks_dict = json.loads(tasks_json) if tasks_json else {}
                except:
                    tasks_dict = {}

                raw_services = [s.strip() for s in pkg_info[1].replace("\n", ",").split(",") if s.strip()] if pkg_info[1] else []
                for srv in raw_services:
                    if srv not in tasks_dict:
                        tasks_dict[srv] = False

                if tasks_dict:
                    updated_tasks = {}
                    completed_count = 0
                    
                    st.write("📌 **Check services upon completion (Tick ✔️):**")
                    
                    for service_name, status in tasks_dict.items():
                        is_done = st.checkbox(service_name, value=status, key=f"task_{selected_id}_{service_name}")
                        updated_tasks[service_name] = is_done
                        if is_done:
                            completed_count += 1
                    
                    total_tasks = len(updated_tasks)
                    progress = completed_count / total_tasks if total_tasks > 0 else 0
                    st.progress(progress)
                    st.caption(f"{t['completion_rate']} {completed_count}/{total_tasks} ({int(progress * 100)}%)")
                    
                    if st.button(t["save_tasks"], type="primary"):
                        c.execute("UPDATE clients SET tasks_status = ? WHERE id = ?", 
                                  (json.dumps(updated_tasks, ensure_ascii=False), selected_id))
                        conn.commit()
                        st.success(t["tasks_saved"])
                        st.rerun()
                else:
                    st.info("No services listed for this package.")
            else:
                st.warning(t["no_pkg_assigned"])
        else:
            st.info(t["no_clients"])
            
        conn.close()

    # --- 5. Log Expense ---
    elif choice == t["expenses"]:
        st.title(f"💸 {t['expenses']}")
        conn = get_db_connection()
        c = conn.cursor()
        
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
                else:
                    st.error(t["exp_err"])
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
                    
                    if st.form_submit_button(t["save"], type="primary"):
                        c.execute("INSERT INTO packages (name, price, details, duration_days, editor_tasks, social_tasks) VALUES (?, ?, ?, ?, ?, ?)", 
                                  (p_name, p_price, p_details, int(p_duration), p_editor_tasks, p_social_tasks))
                        conn.commit()
                        st.success("Package added successfully!")
                        st.rerun()
        
        df_pkgs = pd.read_sql_query("SELECT id, name, price, duration_days, details, editor_tasks, social_tasks FROM packages", conn)
        st.dataframe(df_pkgs, use_container_width=True)
        
        if role == "Owner" and not df_pkgs.empty:
            st.divider()
            st.subheader(f"🗑️ {t['delete_pkg']}")
            pkg_to_delete = st.selectbox("Select Package to delete", df_pkgs["name"].tolist())
            if st.button("Delete Selected Package", type="primary"):
                c.execute("DELETE FROM packages WHERE name = ?", (pkg_to_delete,))
                conn.commit()
                st.success(t["pkg_deleted"])
                st.rerun()
        conn.close()

    # --- 7. Full Audit Sheet (Owner Only) ---
    elif choice == t["audit"] and role == "Owner":
        st.title(f"📊 {t['audit']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        df_exp = pd.read_sql_query("SELECT id, title, amount, category, added_by, date FROM expenses", conn)
        df_inc = pd.read_sql_query("SELECT id, client_name, package_name, amount, added_by, date FROM incomes", conn)
        
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
                'Item' if st.session_state.lang == "EN" else 'البيان': ['Total Revenue', 'Total Expenses', 'Net Profit'] if st.session_state.lang == "EN" else ['إجمالي الإيرادات (الداخل)', 'إجمالي المصروفات (الخارج)', 'صافي الأرباح'],
                'Amount (EGP)': [total_incomes, total_outcomes, net_profit]
            })
            df_summary.to_excel(writer, index=False, sheet_name='Summary')
            df_inc.to_excel(writer, index=False, sheet_name='Incomes')
            df_exp.to_excel(writer, index=False, sheet_name='Expenses')
            
        excel_data = output.getvalue()
        
        st.download_button(
            label=t["export_excel"],
            data=excel_data,
            file_name="focal_craft_financial_audit.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        tab_inc, tab_exp = st.tabs(["🟢 Revenue (Incomes)" if st.session_state.lang == "EN" else "🟢 الإيرادات (الداخل للشركة)", 
                                    "🔴 Expenses (Outcomes)" if st.session_state.lang == "EN" else "🔴 المصروفات (الخارج من الشركة)"])
        
        with tab_inc:
            st.subheader("📋 Client Subscriptions & Revenue List" if st.session_state.lang == "EN" else "📋 قائمة اشتراكات العملاء والإيرادات")
            st.dataframe(df_inc, use_container_width=True)
            
        with tab_exp:
            st.subheader("📋 Operational Expenses List" if st.session_state.lang == "EN" else "📋 قائمة المصروفات التشغيلية")
            st.dataframe(df_exp, use_container_width=True)
            
            if not df_exp.empty:
                st.divider()
                st.subheader(f"🗑️ {t['delete_exp']}")
                exp_to_delete = st.selectbox("Select Expense ID to delete:" if st.session_state.lang == "EN" else "اختر رقم المصروف لمسحه:", df_exp["id"].tolist())
                if st.button("Delete Selected Expense" if st.session_state.lang == "EN" else "مسح المصروف المحدد", type="primary"):
                    c.execute("DELETE FROM expenses WHERE id = ?", (exp_to_delete,))
                    conn.commit()
                    st.success(t["exp_deleted"])
                    st.rerun()
                
        conn.close()
