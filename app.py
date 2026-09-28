import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import base64
import json
import re
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO

# ==========================================
# 1. Page Config & Professional Dark Theme
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

st.set_page_config(
    page_title="Focal Craft Team",
    page_icon=logo_img if logo_img else "🎬",
    layout="wide"
)

# Inject Custom High-End Dark Glassmorphism CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Cairo', 'Inter', sans-serif;
        background-color: #080c14 !important;
        color: #f1f5f9 !important;
    }

    .stApp {
        background: radial-gradient(circle at 50% 0%, #1e1b4b 0%, #0f172a 50%, #080c14 100%) !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #0b0f19 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(15, 23, 42, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.6) !important;
        backdrop-filter: blur(16px) !important;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.8)) !important;
        padding: 18px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3) !important;
    }

    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-weight: 800 !important;
    }

    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
        border: none !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4) !important;
        transition: all 0.3s ease !important;
    }

    .stButton>button[kind="primary"]:hover {
        background: linear-gradient(135deg, #818cf8, #6366f1) !important;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.6) !important;
        transform: translateY(-2px);
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(15, 23, 42, 0.8);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    .stTabs [aria-selected="true"] {
        background-color: #4f46e5 !important;
        color: #ffffff !important;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Database Connection & Schema
# ==========================================
DB_FILE = "/tmp/focal_craft.db"

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    
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
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            details TEXT,
            duration_days INTEGER DEFAULT 30
        )
    ''')
    
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

    # Default Owner
    c.execute("SELECT * FROM users WHERE role = 'Owner'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role, name, salary) VALUES (?, ?, ?, ?, ?)",
                  ("Eng Abdelrhman Osama", hash_pass("#Bedo-1428"), 'Owner', "Eng Abdelrhman Osama", 0.0))
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
# 3. Smart Task AI Engine (Smart Parser)
# ==========================================
def smart_parse_package_details(details_text, client_name):
    """
    مُحرك توجيه المهام الذكي:
    يقرأ التفاصيل العامة للباقة، يفكك الأعداد والأنواع، ويوجه المهام تلقائياً للوظائف المعنية.
    """
    assigned_tasks = []
    if not details_text or not details_text.strip():
        return assigned_tasks

    # تقسيم التفاصيل بناءً على الفواصل أو الأسطر
    lines = [line.strip() for line in re.split(r'[\n,،]+', details_text) if line.strip()]

    # الكلمات المفتاحية الذكية لربط المهام بمهن الموظفين
    keywords_map = {
        "Editor": ["فيديو", "فيديوهات", "مونتاج", "edit", "editor", "video", "reels", "ريلز", "ريل", "shorts"],
        "Social Media Specialist": ["بوست", "بوستات", "منشور", "منشورات", "post", "posts", "سوشيال", "تصميمات", "تصميم غلاف"],
        "Web Designer": ["موقع", "ويب", "ويب سايت", "site", "website", "web", "صفحة هبوط", "landing page", "تصميم موقع"]
    }

    now_full_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    for line in lines:
        # البحث عن أرقام داخل السطر (مثل 30 أو 3)
        match = re.search(r'(\d+)', line)
        count = int(match.group(1)) if match else 1
        count = min(count, 100) # حماية النظام من الأرقام الضخمة جداً

        # تنظيف الوصف من الأرقام
        clean_desc = re.sub(r'\d+', '', line).strip()
        if not clean_desc:
            clean_desc = "Task"

        # تحديد الوظيفة المستهدفة ذكياً
        matched_role = "General / Other"
        line_lower = line.lower()
        
        for role_name, keywords in keywords_map.items():
            if any(kw in line_lower for kw in keywords):
                matched_role = role_name
                break

        # توليد المهام منفصلة وتوزيعها تلقائياً
        for i in range(1, count + 1):
            task_title = f"{clean_desc} #{i}" if count > 1 else clean_desc
            assigned_tasks.append((client_name, matched_role, task_title, now_full_str))

    return assigned_tasks

# ==========================================
# 4. Session State & Language Setup
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "lang" not in st.session_state:
    st.session_state.lang = "EN"

translations = {
    "EN": {
        "title": "Focal Craft Team",
        "subtitle": "Unified AI Management System",
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
        "cs": "Clients & Subscriptions",
        "expenses": "Log Expense",
        "packages": "Packages Hub",
        "employees": "Team & Smart Task Audit",
        "audit": "Financial Audit (Owner)",
        "logout": "Logout",
        "status": "System Status",
        "active": "Active 🟢",
        "add_pkg": "Add New Package",
        "pkg_name": "Package Name",
        "price": "Price (EGP)",
        "pkg_duration": "Duration (Days)",
        "details": "Package Details (e.g. 30 posts, 3 videos, 1 website)",
        "save": "Save Package",
        "add_emp": "➕ Add New Employee",
        "fullname": "Full Name",
        "emp_added": "Employee added successfully!",
        "add_client": "Add New Client",
        "client_name": "Client Name",
        "phone": "Phone Number",
        "select_package": "Select Package",
        "notes": "Notes",
        "client_added": "Client created & tasks intelligently distributed to employees!",
        "clients_list": "Client Subscriptions",
        "track_services": "Service Checklist Tracking",
        "exp_title": "Expense Description",
        "amount": "Amount",
        "category": "Category",
        "log_exp_btn": "Log Expense",
        "delete_pkg": "Delete Package",
        "total_exp": "Total Expenses",
        "total_inc": "Total Revenue",
        "net_profit": "Net Profit",
        "export_excel": "📥 Export Excel Report",
        "col_task_id": "Task ID",
        "col_client": "Client",
        "col_desc": "Task",
        "col_status": "Status",
        "col_created": "Assigned At",
        "col_completed": "Completed At",
        "tasks_for_role": "📌 Automated Tasks For:"
    },
    "AR": {
        "title": "فوكال كرافت تيم",
        "subtitle": "نظام الإدارة الذكي الموحد",
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
        "cs": "إدارة العملاء والاشتراكات",
        "expenses": "تسجيل مصروف",
        "packages": "إدارة الباقات",
        "employees": "الموظفين ومتابعة المهام الذكية",
        "audit": "شيت الحسابات والتدقيق (المالك)",
        "logout": "تسجيل الخروج",
        "status": "حالة النظام",
        "active": "نشط 🟢",
        "add_pkg": "إضافة باقة جديدة",
        "pkg_name": "اسم الباقة",
        "price": "السعر (جنيه)",
        "pkg_duration": "مدة الباقة (بالأيام)",
        "details": "تفاصيل الباقة العامة (مثال: 30 بوست، 3 فيديو، تصميم موقع)",
        "save": "حفظ الباقة",
        "add_emp": "➕ إضافة موظف جديد",
        "fullname": "الاسم الكامل",
        "emp_added": "تمت إضافة الموظف بنجاح!",
        "add_client": "إضافة عميل جديد",
        "client_name": "اسم العميل",
        "phone": "رقم الهاتف",
        "select_package": "اختر الباقة",
        "notes": "ملاحظات",
        "client_added": "تم تسجيل العميل وتحليل وتوزيع المهام تلقائياً على الموظفين!",
        "clients_list": "قائمة العملاء والاشتراكات",
        "track_services": "متابعة تنفيذ خدمات الباقة",
        "exp_title": "بيان المصروف",
        "amount": "المبلغ",
        "category": "القسم",
        "log_exp_btn": "تسجيل المصروف",
        "delete_pkg": "حذف باقة",
        "total_exp": "إجمالي المصروفات",
        "total_inc": "إجمالي الإيرادات",
        "net_profit": "صافي الأرباح",
        "export_excel": "📥 سحب الشيت المالي (Excel)",
        "col_task_id": "رقم المهمة",
        "col_client": "العميل",
        "col_desc": "تفاصيل المهمة",
        "col_status": "الحالة",
        "col_created": "تاريخ التكاليف",
        "col_completed": "تاريخ الإنجاز",
        "tasks_for_role": "📌 المهام الموزعة تلقائياً لوظيفة:"
    }
}

t = translations[st.session_state.lang]

# ==========================================
# 5. Login View
# ==========================================
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        if logo_img:
            st.image(logo_img, width=140)
        st.markdown(f"<h2 style='text-align: center; color: #f8fafc;'>{t['title']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #94a3b8;'>{t['subtitle']}</p>", unsafe_allow_html=True)
        
        selected_lang = st.radio("🌐 Language / اللغة", ["English", "العربية"], 
                                 index=0 if st.session_state.lang == "EN" else 1, horizontal=True)
        st.session_state.lang = "EN" if selected_lang == "English" else "AR"
        t = translations[st.session_state.lang]

        with st.form("login_form"):
            username = st.text_input(t["username"])
            password = st.text_input(t["password"], type="password")
            if st.form_submit_button(t["login_btn"], use_container_width=True, type="primary"):
                user = check_login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_info = {"username": user[0], "role": user[1], "name": user[2]}
                    st.success(t["login_success"])
                    st.rerun()
                else:
                    st.error(t["login_error"])

# ==========================================
# 6. Main Application View
# ==========================================
else:
    with st.sidebar:
        if logo_img:
            st.image(logo_img, use_container_width=True)
        st.markdown(f"<h3 style='color: #f8fafc; margin-bottom: 0;'>{t['title']}</h3>", unsafe_allow_html=True)
        st.caption(f"⚡ {t['subtitle']}")
        st.write(f"{t['welcome']}: **{st.session_state.user_info['name']}**")
        st.caption(f"{t['role']}: `{st.session_state.user_info['role']}`")
        
        lang_choice = st.radio("🌐 Language / اللغة", ["English", "العربية"], 
                               index=0 if st.session_state.lang == "EN" else 1, horizontal=True)
        st.session_state.lang = "EN" if lang_choice == "English" else "AR"
        t = translations[st.session_state.lang]
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

    # --- Home Page ---
    if choice == t["home"]:
        st.title(f"🚀 {t['home']}")
        col1, col2, col3 = st.columns(3)
        col1.metric(t["status"], t["active"])
        col2.metric(t["username"], st.session_state.user_info["username"])
        col3.metric(t["role"], st.session_state.user_info["role"])

    # --- My Assigned Tasks ---
    elif choice == t["my_tasks"]:
        st.title(f"📋 {t['my_tasks']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        user_role = role
        if user_role != "Owner":
            tasks_df = pd.read_sql_query("SELECT * FROM assigned_tasks WHERE assigned_role = ?", conn, params=(user_role,))
        else:
            tasks_df = pd.read_sql_query("SELECT * FROM assigned_tasks", conn)

        pending = tasks_df[tasks_df["status"] == "Pending"] if not tasks_df.empty else pd.DataFrame()
        completed = tasks_df[tasks_df["status"] == "Completed ✅"] if not tasks_df.empty else pd.DataFrame()

        t1, t2 = st.tabs(["⏳ Pending Tasks", "✅ Completed Tasks"])
        with t1:
            if pending.empty:
                st.info("No pending tasks assigned right now! 🎉")
            else:
                for idx, row in pending.iterrows():
                    with st.expander(f"📌 Client: {row['client_name']} — {row['task_description']}"):
                        st.write(f"**Assigned Role:** {row['assigned_role']}")
                        st.write(f"**Date:** {row['created_at']}")
                        if st.button("Mark as Complete ✅", key=f"done_{row['id']}", type="primary"):
                            c.execute("UPDATE assigned_tasks SET status = 'Completed ✅', completed_at = ? WHERE id = ?",
                                      (datetime.now().strftime("%Y-%m-%d %H:%M"), row['id']))
                            conn.commit()
                            st.success("Task Completed!")
                            st.rerun()
        with t2:
            if not completed.empty:
                st.dataframe(completed[["client_name", "assigned_role", "task_description", "completed_at"]], use_container_width=True)
            else:
                st.caption("No completed tasks yet.")
        conn.close()

    # --- Employee Hub & Automated Task Audit ---
    elif choice == t.get("employees") and role in ["Owner", "Manager"]:
        st.title(f"👥 {t['employees']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        tab_emp, tab_tasks = st.tabs(["👤 Employee Directory", "🤖 Automated Task Distribution Audit"])
        
        with tab_emp:
            with st.popover(t["add_emp"], use_container_width=True):
                with st.form("add_emp_form"):
                    u_fullname = st.text_input(t["fullname"])
                    u_username = st.text_input(t["username"])
                    u_password = st.text_input(t["password"], type="password")
                    u_role = st.selectbox(t["role"], ["Editor", "Social Media Specialist", "Web Designer", "Manager", "Owner", "Other"])
                    u_salary = st.number_input("Salary (EGP)", min_value=0.0)
                    if st.form_submit_button("Save Employee", type="primary"):
                        try:
                            c.execute("INSERT INTO users (username, password, role, name, salary) VALUES (?, ?, ?, ?, ?)",
                                      (u_username, hash_pass(u_password), u_role, u_fullname, u_salary))
                            conn.commit()
                            st.success(t["emp_added"])
                            st.rerun()
                        except Exception:
                            st.error("Username already exists!")
            
            users_df = pd.read_sql_query("SELECT id, name, username, role, salary FROM users", conn)
            st.dataframe(users_df, use_container_width=True)

        with tab_tasks:
            st.subheader("📊 Smart Auto-Routed Tasks Overview")
            all_tasks = pd.read_sql_query("SELECT * FROM assigned_tasks", conn)
            if all_tasks.empty:
                st.info("No tasks automatically generated yet.")
            else:
                roles = all_tasks["assigned_role"].unique()
                for r in roles:
                    with st.expander(f"{t['tasks_for_role']} **{r}**", expanded=True):
                        sub = all_tasks[all_tasks["assigned_role"] == r]
                        st.dataframe(sub[["id", "client_name", "task_description", "status", "created_at", "completed_at"]].rename(
                            columns={"id": t["col_task_id"], "client_name": t["col_client"], "task_description": t["col_desc"],
                                     "status": t["col_status"], "created_at": t["col_created"], "completed_at": t["col_completed"]}
                        ), use_container_width=True)
        conn.close()

    # --- Clients & Automated Task Smart Engine Integration ---
    elif choice == t["cs"]:
        st.title(f"📞 {t['cs']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        with st.expander(f"➕ {t['add_client']}"):
            with st.form("add_client_form"):
                c_name = st.text_input(t["client_name"])
                c_phone = st.text_input(t["phone"])
                
                pkgs = pd.read_sql_query("SELECT id, name, price, details FROM packages", conn)
                pkg_options = {f"{row['name']} ({row['price']:,.0f} EGP)": (row['id'], row['price'], row['details'], row['name']) for _, row in pkgs.iterrows()} if not pkgs.empty else {}
                
                selected_pkg = st.selectbox(t["select_package"], list(pkg_options.keys()) if pkg_options else ["N/A"])
                c_notes = st.text_area(t["notes"])
                
                if st.form_submit_button("Create Client & Auto-Route Tasks", type="primary"):
                    if c_name and pkg_options:
                        pkg_id, pkg_price, pkg_details, pkg_name = pkg_options[selected_pkg]
                        current_date = datetime.now().strftime("%Y-%m-%d")
                        
                        # 1. Insert Client
                        c.execute("INSERT INTO clients (client_name, phone, package_id, notes, created_at) VALUES (?, ?, ?, ?, ?)",
                                  (c_name, c_phone, pkg_id, c_notes, current_date))
                        
                        # 2. Log Income
                        c.execute("INSERT INTO incomes (client_name, package_name, amount, added_by) VALUES (?, ?, ?, ?)",
                                  (c_name, pkg_name, pkg_price, st.session_state.user_info["name"]))
                        
                        # 3. AI Smart Task Parsing & Automated Role Routing
                        generated_tasks = smart_parse_package_details(pkg_details, c_name)
                        for task in generated_tasks:
                            c.execute("INSERT INTO assigned_tasks (client_name, assigned_role, task_description, created_at) VALUES (?, ?, ?, ?)", task)

                        conn.commit()
                        st.success(t["client_added"])
                        st.rerun()

        clients = pd.read_sql_query('''
            SELECT c.id, c.client_name, c.phone, p.name as package, p.price, c.created_at, c.notes 
            FROM clients c LEFT JOIN packages p ON c.package_id = p.id
        ''', conn)
        st.dataframe(clients, use_container_width=True)
        conn.close()

    # --- Packages Hub (Simplified & Smart) ---
    elif choice == t["packages"]:
        st.title(f"📦 {t['packages']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        if role == "Owner":
            with st.expander(f"➕ {t['add_pkg']}"):
                with st.form("add_pkg_form"):
                    p_name = st.text_input(t["pkg_name"])
                    p_price = st.number_input(t["price"], min_value=0.0)
                    p_duration = st.number_input(t["pkg_duration"], min_value=1, value=30)
                    p_details = st.text_area(t["details"], help="اكتب تفاصيل الباقة هنا بصورة طبيعية مثل: 30 بوست، 3 فيديوهات، 1 تصميم موقع")
                    
                    if st.form_submit_button(t["save"], type="primary"):
                        c.execute("INSERT INTO packages (name, price, details, duration_days) VALUES (?, ?, ?, ?)",
                                  (p_name, p_price, p_details, int(p_duration)))
                        conn.commit()
                        st.success("Package added successfully!")
                        st.rerun()

        pkgs_df = pd.read_sql_query("SELECT id, name, price, duration_days, details FROM packages", conn)
        st.dataframe(pkgs_df, use_container_width=True)
        
        if role == "Owner" and not pkgs_df.empty:
            st.divider()
            pkg_del = st.selectbox("Select Package to Delete", pkgs_df["name"].tolist())
            if st.button(t["delete_pkg"], type="primary"):
                c.execute("DELETE FROM packages WHERE name = ?", (pkg_del,))
                conn.commit()
                st.success("Package deleted!")
                st.rerun()
        conn.close()

    # --- Log Expense ---
    elif choice == t["expenses"]:
        st.title(f"💸 {t['expenses']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        with st.form("exp_form"):
            e_title = st.text_input(t["exp_title"])
            e_amt = st.number_input(t["amount"], min_value=0.0)
            e_cat = st.selectbox(t["category"], ["Operational", "Salaries", "Marketing", "Other"])
            if st.form_submit_button(t["log_exp_btn"], type="primary"):
                if e_title and e_amt > 0:
                    c.execute("INSERT INTO expenses (title, amount, category, added_by) VALUES (?, ?, ?, ?)",
                              (e_title, e_amt, e_cat, st.session_state.user_info["name"]))
                    conn.commit()
                    st.success("Expense recorded!")
        conn.close()

    # --- Financial Audit Sheet (Owner Only) ---
    elif choice == t["audit"] and role == "Owner":
        st.title(f"📊 {t['audit']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        df_exp = pd.read_sql_query("SELECT * FROM expenses", conn)
        df_inc = pd.read_sql_query("SELECT * FROM incomes", conn)
        
        tot_exp = df_exp['amount'].sum() if not df_exp.empty else 0.0
        tot_inc = df_inc['amount'].sum() if not df_inc.empty else 0.0
        net = tot_inc - tot_exp
        
        c1, c2, c3 = st.columns(3)
        c1.metric(t["total_inc"], f"{tot_inc:,.2f} EGP")
        c2.metric(t["total_exp"], f"{tot_exp:,.2f} EGP")
        c3.metric(t["net_profit"], f"{net:,.2f} EGP")
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_inc.to_excel(writer, index=False, sheet_name='Incomes')
            df_exp.to_excel(writer, index=False, sheet_name='Expenses')
        
        st.download_button(t["export_excel"], data=output.getvalue(), file_name="audit_sheet.xlsx", use_container_width=True)
        conn.close()
