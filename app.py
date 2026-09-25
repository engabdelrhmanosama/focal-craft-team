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

# --- Hide Streamlit Header & GitHub Icon ---
hide_github_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppHeader {display: none;}
    </style>
"""
st.markdown(hide_github_style, unsafe_allow_html=True)

def get_image_base64(image_path):
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

logo_base64 = get_image_base64(logo_path)

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
            name TEXT NOT NULL
        )
    ''')
    
    # Packages Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            details TEXT,
            duration_days INTEGER DEFAULT 30
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
    
    # Expenses Table (Outcomes / المصروفات)
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

    # Incomes Table (Incomes / الإيرادات والداخل للشركة)
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
    c.execute("PRAGMA table_info(packages)")
    pkg_cols = [col[1] for col in c.fetchall()]
    if 'duration_days' not in pkg_cols:
        try:
            c.execute("ALTER TABLE packages ADD COLUMN duration_days INTEGER DEFAULT 30")
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
        c.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
                  (owner_username, default_password, 'Owner', owner_username))
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
    st.session_state.lang = "EN"
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
            background-color: #e2e8f0 !important;
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
        "cs": "Clients & Services Tracking",
        "expenses": "Log Expense",
        "packages": "Packages Management",
        "employees": "Users Management",
        "audit": "Financial Audit & Sheets (Owner Only)",
        "logout": "Logout",
        "status": "System Status",
        "active": "Active 🟢",
        "add_pkg": "Add New Package",
        "pkg_name": "Package Name",
        "price": "Price",
        "pkg_duration": "Package Duration (Days)",
        "details": "Package Services (Separate with commas or new lines)",
        "save": "Save",
        "add_emp": "Add New User",
        "fullname": "Full Name",
        "emp_added": "User added successfully!",
        "user_exists": "Username or ID already exists!",
        "delete": "Delete",
        "edit": "Edit User Details, ID & Password",
        "add_client": "Add New Client",
        "client_name": "Client Name",
        "phone": "Phone Number",
        "select_package": "Select Package",
        "notes": "Notes",
        "client_added": "Client added and income logged successfully!",
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
        "select_user_edit": "Select user to edit",
        "edit_id": "Edit User ID",
        "new_username": "New Username",
        "new_role": "New Role",
        "new_pw": "New Password (Leave blank to keep unchanged)",
        "save_user_changes": "Save User Changes",
        "user_updated": "User details and password updated successfully!",
        "delete_user": "Delete User",
        "user_deleted": "User deleted successfully!",
        "total_exp": "Total Expenses (Outcomes)",
        "total_inc": "Total Revenue (Incomes)",
        "net_profit": "Net Profit",
        "export_excel": "📥 Export Full Audit Report (Excel)",
        "delete_exp": "Delete Expense",
        "exp_deleted": "Expense deleted successfully!",
        "no_clients": "No clients registered yet.",
        "no_pkg_assigned": "Client is not assigned to any package.",
        "completion_rate": "Service Completion Rate:",
        "delete_client": "Delete Client (Owner Only)",
        "client_deleted": "Client deleted successfully!"
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
        "cs": "إدارة العملاء ومتابعة الخدمات",
        "expenses": "تسجيل مصروف",
        "packages": "إدارة الباقات",
        "employees": "إدارة المستخدمين",
        "audit": "شيت الحسابات والتدقيق المالي (المالك فقط)",
        "logout": "تسجيل الخروج",
        "status": "حالة النظام",
        "active": "نشط 🟢",
        "add_pkg": "إضافة باقة جديدة",
        "pkg_name": "اسم الباقة",
        "price": "السعر",
        "pkg_duration": "مدة الباقة (بالأيام)",
        "details": "تفاصيل الخدمات (افصل بين كل خدمة بفاصلة أو سطر جديد)",
        "save": "حفظ",
        "add_emp": "إضافة مستخدم جديد",
        "fullname": "الاسم الكامل",
        "emp_added": "تمت إضافة المستخدم بنجاح!",
        "user_exists": "اسم المستخدم أو ID موجود بالفعل!",
        "delete": "حذف",
        "edit": "تعديل البيانات، الـ ID وكلمة المرور",
        "add_client": "إضافة عميل جديد",
        "client_name": "اسم العميل",
        "phone": "رقم الهاتف",
        "select_package": "اختر الباقة",
        "notes": "ملاحظات",
        "client_added": "تمت إضافة العميل وتسجيل دخل الباقة تلقائياً في الشيت!",
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
        "select_user_edit": "اختر المستخدم للتعديل",
        "edit_id": "تعديل رقم الـ ID",
        "new_username": "اسم المستخدم الجديد",
        "new_role": "الرتبة الجديدة",
        "new_pw": "كلمة المرور الجديدة (اتركها فارغة إذا لا تريد التغيير)",
        "save_user_changes": "حفظ جميع التعديلات",
        "user_updated": "تم تحديث بيانات المستخدم والرقم السري بنجاح!",
        "delete_user": "حذف مستخدم",
        "user_deleted": "تم حذف المستخدم بنجاح!",
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
        "client_deleted": "تم حذف العميل بنجاح!"
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
        st.markdown(f"<h2 style='text-align: center;'>{t['title']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center;'>{t['subtitle']}</p>", unsafe_allow_html=True)
        
        col_lang, col_theme = st.columns(2)
        with col_lang:
            selected_lang = st.radio("🌐 Language / اللغة", ["English", "العربية"], horizontal=True)
            st.session_state.lang = "EN" if selected_lang == "English" else "AR"
            t = translations[st.session_state.lang]
        with col_theme:
            theme_choice = st.radio("☀️ Theme / المظهر", ["Dark", "Light"], horizontal=True)
            st.session_state.theme = theme_choice

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
# 5. Main Dashboard
# ==========================================
else:
    with st.sidebar:
        if logo_img:
            st.image(logo_img, use_container_width=True)
        st.title(t["title"])
        st.write(f"{t['welcome']}: **{st.session_state.user_info['name']}**")
        st.caption(f"{t['role']}: {st.session_state.user_info['role']}")
        
        lang_choice = st.radio("🌐 Language / اللغة", ["English", "العربية"], 
                               index=0 if st.session_state.lang == "EN" else 1, horizontal=True)
        st.session_state.lang = "EN" if lang_choice == "English" else "AR"
        t = translations[st.session_state.lang]
        
        theme_toggle = st.radio("☀️ Theme / المظهر", ["Dark 🌙", "Light ☀️"], 
                                index=0 if st.session_state.theme == "Dark" else 1, horizontal=True)
        st.session_state.theme = "Dark" if "Dark" in theme_toggle else "Light"
        
        st.divider()
        
        role = st.session_state.user_info["role"]
        menu_options = [t["home"], t["cs"], t["expenses"], t["packages"]]
        if role == "Owner":
            menu_options.extend([t["employees"], t["audit"]])
            
        choice = st.radio(t["nav"], menu_options)
        
        st.divider()
        if st.button(t["logout"], use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()

    # --- 1. Home Page ---
    if choice == t["home"]:
        st.title(f"🎬 {t['home']}")
        st.write(f"{t['welcome']} {st.session_state.user_info['name']}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric(t["status"], t["active"])
        col2.metric(t["username"], st.session_state.user_info["username"])
        col3.metric(t["role"], st.session_state.user_info["role"])

    # --- 2. Clients & Services Checklist Tracking ---
    elif choice == t["cs"]:
        st.title(f"📞 {t['cs']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        # Add Client Form
        with st.expander(f"➕ {t['add_client']}"):
            with st.form("add_client_form"):
                c_name = st.text_input(t["client_name"])
                c_phone = st.text_input(t["phone"])
                
                pkgs = pd.read_sql_query("SELECT id, name, price, details FROM packages", conn)
                pkg_options = {f"{row['name']} ({row['price']:,.0f} EGP)": (row['id'], row['price'], row['details'], row['name']) for _, row in pkgs.iterrows()} if not pkgs.empty else {}
                
                selected_pkg_str = st.selectbox(t["select_package"], list(pkg_options.keys()) if pkg_options else ["N/A"])
                c_notes = st.text_area(t["notes"])
                
                if st.form_submit_button(t["save"]):
                    if c_name and pkg_options:
                        pkg_id, pkg_price, pkg_details, pkg_name = pkg_options[selected_pkg_str]
                        
                        initial_tasks = {}
                        if pkg_details:
                            services = [s.strip() for s in pkg_details.replace("\n", ",").split(",") if s.strip()]
                            for service in services:
                                initial_tasks[service] = False
                        
                        current_date_str = datetime.now().strftime("%Y-%m-%d")
                        
                        # 1. Insert Client Record
                        c.execute("INSERT INTO clients (client_name, phone, package_id, notes, tasks_status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                                  (c_name, c_phone, pkg_id, c_notes, json.dumps(initial_tasks, ensure_ascii=False), current_date_str))
                        
                        # 2. Insert Income Record (تسجيل الدخل والداخل للشركة تلقائياً)
                        c.execute("INSERT INTO incomes (client_name, package_name, amount, added_by) VALUES (?, ?, ?, ?)",
                                  (c_name, pkg_name, pkg_price, st.session_state.user_info["name"]))
                        
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
                            days_left_list.append(f"{remaining} يوم")
                            status_list.append("نشط 🟢")
                        else:
                            days_left_list.append("0 يوم")
                            status_list.append("منتهي 🔴")
                    except Exception:
                        days_left_list.append("غير محدد")
                        status_list.append("نشط 🟢")
                else:
                    days_left_list.append("غير محدد")
                    status_list.append("نشط 🟢")
            
            df_clients['المتبقي من الباقة'] = days_left_list
            df_clients['حالة الاشتراك'] = status_list

        st.subheader(f"📋 {t['clients_list']}")
        st.dataframe(df_clients, use_container_width=True)
        
        # --- Delete Client (Owner Only) ---
        if role == "Owner" and not df_clients.empty:
            st.divider()
            st.subheader(f"🗑️ {t['delete_client']}")
            client_options = {f"{row['id']} - {row['client_name']}": row['id'] for _, row in df_clients.iterrows()}
            selected_client_del = st.selectbox("اختر العميل المراد حذفه نهائياً:", list(client_options.keys()))
            
            if st.button("حذف العميل المحدد ❌", type="primary"):
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
                    
                    if st.button(t["save_tasks"]):
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

    # --- 3. Log Expense ---
    elif choice == t["expenses"]:
        st.title(f"💸 {t['expenses']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        with st.form("add_expense_form"):
            e_title = st.text_input(t["exp_title"])
            e_amount = st.number_input(t["amount"], min_value=0.0)
            e_cat = st.selectbox(t["category"], ["Operational / تشغيلي", "Equipment / معدات", "Marketing / تسويق", "Salaries / رواتب", "Other / أخرى"])
            
            if st.form_submit_button(t["log_exp_btn"]):
                if e_title and e_amount > 0:
                    c.execute("INSERT INTO expenses (title, amount, category, added_by) VALUES (?, ?, ?, ?)",
                              (e_title, e_amount, e_cat, st.session_state.user_info["name"]))
                    conn.commit()
                    st.success(t["exp_saved"])
                else:
                    st.error(t["exp_err"])
        conn.close()

    # --- 4. Packages Management ---
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
                    if st.form_submit_button(t["save"]):
                        c.execute("INSERT INTO packages (name, price, details, duration_days) VALUES (?, ?, ?, ?)", 
                                  (p_name, p_price, p_details, int(p_duration)))
                        conn.commit()
                        st.success("Package added successfully!")
                        st.rerun()
        
        df_pkgs = pd.read_sql_query("SELECT id, name, price, duration_days, details FROM packages", conn)
        st.dataframe(df_pkgs, use_container_width=True)
        
        if role == "Owner" and not df_pkgs.empty:
            st.divider()
            st.subheader(f"🗑️ {t['delete_pkg']}")
            pkg_to_delete = st.selectbox("Select Package to delete", df_pkgs["name"].tolist())
            if st.button("Delete Selected Package"):
                c.execute("DELETE FROM packages WHERE name = ?", (pkg_to_delete,))
                conn.commit()
                st.success(t["pkg_deleted"])
                st.rerun()
        conn.close()

    # --- 5. Users Management ---
    elif choice == t["employees"] and role == "Owner":
        st.title(f"👥 {t['employees']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        # Add New User
        with st.expander(f"➕ {t['add_emp']}"):
            with st.form("add_user_form"):
                u_name = st.text_input(t["fullname"])
                u_username = st.text_input(t["username"])
                u_password = st.text_input(t["password"], type="password")
                u_role = st.selectbox(t["role"], ["Customer Service", "Editor", "Moderator", "Owner"])
                if st.form_submit_button(t["save"]):
                    try:
                        c.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
                                  (u_username, hash_pass(u_password), u_role, u_name))
                        conn.commit()
                        st.success(t["emp_added"])
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(t["user_exists"])
        
        df_users = pd.read_sql_query("SELECT id, name, username, role FROM users", conn)
        st.dataframe(df_users, use_container_width=True)
        
        st.divider()
        col_edit, col_del = st.columns(2)
        
        # Edit ID, Username & Password
        with col_edit:
            st.subheader("✏️ " + t["edit"])
            user_list = df_users["username"].tolist()
            selected_user = st.selectbox(t["select_user_edit"], user_list)
            
            c.execute("SELECT id, username, role, name FROM users WHERE username = ?", (selected_user,))
            current_user_data = c.fetchone()
            
            new_id = st.number_input(t["edit_id"], value=int(current_user_data[0]), step=1)
            new_username = st.text_input(t["new_username"], value=current_user_data[1])
            new_fullname = st.text_input(t["fullname"], value=current_user_data[3])
            new_role = st.selectbox(t["new_role"], ["Customer Service", "Editor", "Moderator", "Owner"], 
                                    index=["Customer Service", "Editor", "Moderator", "Owner"].index(current_user_data[2]))
            new_password = st.text_input(t["new_pw"], type="password")
            
            if st.button(t["save_user_changes"]):
                try:
                    if new_password.strip() != "":
                        c.execute("UPDATE users SET id = ?, username = ?, name = ?, role = ?, password = ? WHERE username = ?", 
                                  (new_id, new_username, new_fullname, new_role, hash_pass(new_password), selected_user))
                    else:
                        c.execute("UPDATE users SET id = ?, username = ?, name = ?, role = ? WHERE username = ?", 
                                  (new_id, new_username, new_fullname, new_role, selected_user))
                    conn.commit()
                    st.success(t["user_updated"])
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error(t["user_exists"])

        # Delete User
        with col_del:
            st.subheader("🗑️ " + t["delete_user"])
            user_to_del = st.selectbox("Select user to delete", [u for u in user_list if u != st.session_state.user_info["username"]])
            if st.button("Delete User"):
                c.execute("DELETE FROM users WHERE username = ?", (user_to_del,))
                conn.commit()
                st.success(t["user_deleted"])
                st.rerun()
                
        conn.close()

    # --- 6. Expenses, Incomes & Full Audit Sheet (Owner Only) ---
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
        
        # Excel Export Setup
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_summary = pd.DataFrame({
                'البيان': ['إجمالي الإيرادات (الداخل)', 'إجمالي المصروفات (الخارج)', 'صافي الأرباح'],
                'المبلغ (EGP)': [total_incomes, total_outcomes, net_profit]
            })
            df_summary.to_excel(writer, index=False, sheet_name='الملخص المالي')
            df_inc.to_excel(writer, index=False, sheet_name='الإيرادات (الداخل)')
            df_exp.to_excel(writer, index=False, sheet_name='المصروفات (الخارج)')
            
        excel_data = output.getvalue()
        
        st.download_button(
            label=t["export_excel"],
            data=excel_data,
            file_name="focal_craft_financial_audit.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        tab_inc, tab_exp = st.tabs(["🟢 الإيرادات (الداخل للشركة)", "🔴 المصروفات (الخارج من الشركة)"])
        
        with tab_inc:
            st.subheader("📋 قائمة اشتراكات العملاء والإيرادات")
            st.dataframe(df_inc, use_container_width=True)
            
        with tab_exp:
            st.subheader("📋 قائمة المصروفات التشغيلية")
            st.dataframe(df_exp, use_container_width=True)
            
            if not df_exp.empty:
                st.divider()
                st.subheader(f"🗑️ {t['delete_exp']}")
                exp_to_delete = st.selectbox("اختر رقم المصروف لمسحه:", df_exp["id"].tolist())
                if st.button("مسح المصروف المحدد"):
                    c.execute("DELETE FROM expenses WHERE id = ?", (exp_to_delete,))
                    conn.commit()
                    st.success(t["exp_deleted"])
                    st.rerun()
                
        conn.close()
