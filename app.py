import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import base64
from PIL import Image
from io import BytesIO

# ==========================================
# 1. إعدادات الصفحة والاسم والأيقونة
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

# ==========================================
# 2. قواعد البيانات (SQLite)
# ==========================================
DB_FILE = "/tmp/focal_craft.db"

def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
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
    # جدول العملاء
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            phone TEXT,
            package_id INTEGER,
            notes TEXT,
            FOREIGN KEY (package_id) REFERENCES packages (id)
        )
    ''')
    # جدول المصروفات
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
    
    # حساب الأدمن الافتراضي
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        hashed_pw = hash_pass("admin123")
        c.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
                  ('admin', hashed_pw, 'Owner', 'Eng Abdelrhman Osama'))
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
# 3. إدارة الجلسة واللغات والأنماط (Dark/Light)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "lang" not in st.session_state:
    st.session_state.lang = "EN"
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

# تطبيق الوضع الصباحي أو الليلي
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
        "cs": "Clients Management",
        "expenses": "Log Expense",
        "packages": "Packages Management",
        "employees": "Users Management",
        "audit": "Expenses & Audit (Owner Only)",
        "logout": "Logout",
        "status": "System Status",
        "active": "Active 🟢",
        "add_pkg": "Add New Package",
        "pkg_name": "Package Name",
        "price": "Price",
        "details": "Details",
        "save": "Save",
        "add_emp": "Add New User",
        "fullname": "Full Name",
        "emp_added": "User added successfully!",
        "user_exists": "Username already exists!",
        "delete": "Delete",
        "edit": "Edit User Details & Password",
        "add_client": "Add New Client",
        "client_name": "Client Name",
        "phone": "Phone Number",
        "select_package": "Select Package",
        "notes": "Notes",
        "client_added": "Client added successfully!"
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
        "cs": "إدارة العملاء",
        "expenses": "تسجيل مصروف",
        "packages": "إدارة الباقات",
        "employees": "إدارة المستخدمين",
        "audit": "شيت المصروفات والتدقيق (المالك فقط)",
        "logout": "تسجيل الخروج",
        "status": "حالة النظام",
        "active": "نشط 🟢",
        "add_pkg": "إضافة باقة جديدة",
        "pkg_name": "اسم الباقة",
        "price": "السعر",
        "details": "التفاصيل",
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
        "client_added": "تمت إضافة العميل بنجاح!"
    }
}

t = translations[st.session_state.lang]

# ==========================================
# 4. واجهة تسجيل الدخول (Login Screen)
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
# 5. الواجهة الرئيسية (Dashboard)
# ==========================================
else:
    with st.sidebar:
        if logo_img:
            st.image(logo_img, use_container_width=True)
        st.title(t["title"])
        st.write(f"{t['welcome']}: **{st.session_state.user_info['name']}**")
        st.caption(f"{t['role']}: {st.session_state.user_info['role']}")
        
        # التحكم باللغة والمظهر
        lang_choice = st.radio("🌐 اللغة", ["English", "العربية"], 
                               index=0 if st.session_state.lang == "EN" else 1, horizontal=True)
        st.session_state.lang = "EN" if lang_choice == "English" else "AR"
        t = translations[st.session_state.lang]
        
        theme_toggle = st.radio("☀️ المظهر", ["Dark 🌙", "Light ☀️"], 
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

    # --- 1. الصفحة الرئيسية ---
    if choice == t["home"]:
        st.title(f"🎬 {t['home']}")
        st.write(f"{t['welcome']} {st.session_state.user_info['name']}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric(t["status"], t["active"])
        col2.metric(t["username"], st.session_state.user_info["username"])
        col3.metric(t["role"], st.session_state.user_info["role"])

    # --- 2. إدارة العملاء ---
    elif choice == t["cs"]:
        st.title(f"📞 {t['cs']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        with st.expander(f"➕ {t['add_client']}"):
            with st.form("add_client_form"):
                c_name = st.text_input(t["client_name"])
                c_phone = st.text_input(t["phone"])
                
                pkgs = pd.read_sql_query("SELECT id, name FROM packages", conn)
                pkg_options = {row['name']: row['id'] for _, row in pkgs.iterrows()} if not pkgs.empty else {}
                
                selected_pkg_name = st.selectbox(t["select_package"], list(pkg_options.keys()) if pkg_options else ["لا توجد باقات متاحة"])
                c_notes = st.text_area(t["notes"])
                
                if st.form_submit_button(t["save"]):
                    if c_name and pkg_options:
                        pkg_id = pkg_options[selected_pkg_name]
                        c.execute("INSERT INTO clients (client_name, phone, package_id, notes) VALUES (?, ?, ?, ?)",
                                  (c_name, c_phone, pkg_id, c_notes))
                        conn.commit()
                        st.success(t["client_added"])
                        st.rerun()
                    elif not pkg_options:
                        st.error("يرجى التواصل مع المالك لإضافة باقات أولاً!")

        df_clients = pd.read_sql_query('''
            SELECT c.id, c.client_name, c.phone, p.name as package_name, p.price, c.notes 
            FROM clients c 
            LEFT JOIN packages p ON c.package_id = p.id
        ''', conn)
        conn.close()
        st.dataframe(df_clients, use_container_width=True)

    # --- 3. تسجيل مصروف جديد ---
    elif choice == t["expenses"]:
        st.title(f"💸 {t['expenses']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        with st.form("add_expense_form"):
            e_title = st.text_input("بيان المصروف (السبب/الوصف)")
            e_amount = st.number_input("المبلغ", min_value=0.0)
            e_cat = st.selectbox("القسم", ["تشغيلي", "معدات", "تسويق", "رواتب", "أخرى"])
            
            if st.form_submit_button("تسجيل المصروف"):
                if e_title and e_amount > 0:
                    c.execute("INSERT INTO expenses (title, amount, category, added_by) VALUES (?, ?, ?, ?)",
                              (e_title, e_amount, e_cat, st.session_state.user_info["name"]))
                    conn.commit()
                    st.success("تم تسجيل المصروف بنجاح!")
                else:
                    st.error("يرجى إدخال المبلغ والبيان بشكل صحيح.")
        conn.close()

    # --- 4. إدارة الباقات ---
    elif choice == t["packages"]:
        st.title(f"📦 {t['packages']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        if role == "Owner":
            with st.expander(f"➕ {t['add_pkg']}"):
                with st.form("add_package_form"):
                    p_name = st.text_input(t["pkg_name"])
                    p_price = st.number_input(t["price"], min_value=0.0)
                    p_details = st.text_area(t["details"])
                    if st.form_submit_button(t["save"]):
                        c.execute("INSERT INTO packages (name, price, details) VALUES (?, ?, ?)", 
                                  (p_name, p_price, p_details))
                        conn.commit()
                        st.success("تمت إضافة الباقة بنجاح!")
                        st.rerun()
        
        df_pkgs = pd.read_sql_query("SELECT id, name, price, details FROM packages", conn)
        st.dataframe(df_pkgs, use_container_width=True)
        
        if role == "Owner" and not df_pkgs.empty:
            st.divider()
            st.subheader("🗑️ حذف باقة")
            pkg_to_delete = st.selectbox("اختر الباقة للحذف", df_pkgs["name"].tolist())
            if st.button("حذف الباقة المختارة"):
                c.execute("DELETE FROM packages WHERE name = ?", (pkg_to_delete,))
                conn.commit()
                st.success("تم حذف الباقة بنجاح!")
                st.rerun()
        conn.close()

    # --- 5. إدارة المستخدمين (تعديل الـ ID، الباسورد، اسم المستخدم) ---
    elif choice == t["employees"] and role == "Owner":
        st.title(f"👥 {t['employees']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        # إضافة مستخدم جديد
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
        
        # تعديل الـ ID، اسم المستخدم، والرقم السري
        with col_edit:
            st.subheader("✏️ " + t["edit"])
            user_list = df_users["username"].tolist()
            selected_user = st.selectbox("اختر المستخدم للتعديل", user_list)
            
            # جلب البيانات الحالية للمستخدم
            c.execute("SELECT id, username, role FROM users WHERE username = ?", (selected_user,))
            current_user_data = c.fetchone()
            
            new_id = st.number_input("تعديل رقم الـ ID", value=int(current_user_data[0]), step=1)
            new_username = st.text_input("اسم المستخدم الجديد (Username)", value=current_user_data[1])
            new_role = st.selectbox("الرتبة الجديدة", ["Customer Service", "Editor", "Moderator", "Owner"], 
                                    index=["Customer Service", "Editor", "Moderator", "Owner"].index(current_user_data[2]))
            new_password = st.text_input("كلمة المرور الجديدة (اتركها فارغة إذا لا تريد التغيير)", type="password")
            
            if st.button("حفظ جميع التعديلات"):
                try:
                    if new_password.strip() != "":
                        c.execute("UPDATE users SET id = ?, username = ?, role = ?, password = ? WHERE username = ?", 
                                  (new_id, new_username, new_role, hash_pass(new_password), selected_user))
                    else:
                        c.execute("UPDATE users SET id = ?, username = ?, role = ? WHERE username = ?", 
                                  (new_id, new_username, new_role, selected_user))
                    conn.commit()
                    st.success("تم تحديث بيانات المستخدم والرقم السري بنجاح!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("رقم الـ ID أو اسم المستخدم الجديد مستخدم بالفعل!")

        # حذف مستخدم
        with col_del:
            st.subheader("🗑️ " + t["delete"])
            user_to_del = st.selectbox("اختر المستخدم للحذف", [u for u in user_list if u != "admin"])
            if st.button("حذف المستخدم"):
                c.execute("DELETE FROM users WHERE username = ?", (user_to_del,))
                conn.commit()
                st.success("تم حذف المستخدم بنجاح!")
                st.rerun()
                
        conn.close()

    # --- 6. شيت المصروفات والتدقيق (خاص بـ Owner فقط) ---
    elif choice == t["audit"] and role == "Owner":
        st.title(f"📊 {t['audit']}")
        conn = get_db_connection()
        c = conn.cursor()
        
        df_exp = pd.read_sql_query("SELECT id, title, amount, category, added_by, date FROM expenses", conn)
        
        col1, col2 = st.columns([3, 1])
        col1.metric("إجمالي المصروفات", f"{df_exp['amount'].sum() if not df_exp.empty else 0:,.2f} EGP")
        
        if not df_exp.empty:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_exp.to_excel(writer, index=False, sheet_name='المصروفات')
            excel_data = output.getvalue()
            
            col2.download_button(
                label="📥 سحب شيت المصروفات (Excel)",
                data=excel_data,
                file_name="expenses_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
        st.dataframe(df_exp, use_container_width=True)
        
        if not df_exp.empty:
            st.divider()
            st.subheader("🗑️ مسح مصروف محدد")
            exp_to_delete = st.selectbox("اختر رقم المصروف لمسحه", df_exp["id"].tolist())
            if st.button("حذف المصروف المحدد"):
                c.execute("DELETE FROM expenses WHERE id = ?", (exp_to_delete,))
                conn.commit()
                st.success("تم مسح المصروف بنجاح!")
                st.rerun()
                
        conn.close()
