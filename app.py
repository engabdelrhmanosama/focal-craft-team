import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
import base64
import json
import re
from datetime import datetime
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
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-End Dark UI & Top Navigation Styling
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

    /* Hide Sidebar Completely */
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* Card Styling */
    .emp-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.95)) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(12px) !important;
        margin-bottom: 20px !important;
    }

    .emp-title {
        color: #38bdf8 !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        margin-bottom: 8px !important;
    }

    .emp-badge {
        background-color: #4f46e5 !important;
        color: #ffffff !important;
        padding: 4px 12px !important;
        border-radius: 20px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        display: inline-block !important;
        margin-bottom: 12px !important;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.8)) !important;
        padding: 18px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
    }

    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
        border: none !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.4) !important;
    }

    /* Top Navigation Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(15, 23, 42, 0.85);
        padding: 10px 14px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 25px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #4f46e5 !important;
        color: #ffffff !important;
        border-radius: 10px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Database Connection & Setup
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
# 3. Smart Task AI Parser
# ==========================================
def smart_parse_package_details(details_text, client_name):
    assigned_tasks = []
    if not details_text or not details_text.strip():
        return assigned_tasks

    lines = [line.strip() for line in re.split(r'[\n,،]+', details_text) if line.strip()]

    keywords_map = {
        "Editor": ["فيديو", "فيديوهات", "مونتاج", "edit", "editor", "video", "reels", "ريلز", "ريل", "shorts"],
        "Social Media Specialist": ["بوست", "بوستات", "منشور", "منشورات", "post", "posts", "سوشيال", "تصميمات", "تصميم غلاف"],
        "Web Designer": ["موقع", "ويب", "ويب سايت", "site", "website", "web", "صفحة هبوط", "landing page", "تصميم موقع"]
    }

    now_full_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    for line in lines:
        match = re.search(r'(\d+)', line)
        count = int(match.group(1)) if match else 1
        count = min(count, 100)

        clean_desc = re.sub(r'\d+', '', line).strip()
        if not clean_desc:
            clean_desc = "Task"

        matched_role = "General / Other"
        line_lower = line.lower()
        
        for role_name, keywords in keywords_map.items():
            if any(kw in line_lower for kw in keywords):
                matched_role = role_name
                break

        for i in range(1, count + 1):
            task_title = f"{clean_desc} #{i}" if count > 1 else clean_desc
            assigned_tasks.append((client_name, matched_role, task_title, now_full_str))

    return assigned_tasks

# ==========================================
# 4. Session State Setup
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# ==========================================
# 5. Login View
# ==========================================
if not st.session_state.logged_in:
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        if logo_img:
            st.image(logo_img, width=150)
        st.markdown("<h2 style='text-align: center;'>شركة فوكال كرافت - Focal Craft</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>نظام الإدارة الموحد والمهام الذكية</p>", unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password")
            if st.form_submit_button("تسجيل الدخول", use_container_width=True, type="primary"):
                user = check_login(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_info = {"username": user[0], "role": user[1], "name": user[2]}
                    st.success("تم تسجيل الدخول بنجاح!")
                    st.rerun()
                else:
                    st.error("اسم المستخدم أو كلمة المرور غير صحيحة")

# ==========================================
# 6. Main Application View
# ==========================================
else:
    # Top Header Bar
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.markdown(f"### 🎬 Focal Craft System | مرحباً بك: **{st.session_state.user_info['name']}** (`{st.session_state.user_info['role']}`)")
    with head_col2:
        if st.button("🚪 تسجيل الخروج", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.user_info = None
            st.rerun()

    role = st.session_state.user_info["role"]

    # Top Professional Navigation Menu Tabs
    tabs_list = ["🏠 الرئيسية", "📋 مهامي والشغل المطلوب"]
    if role in ["Owner", "Manager"]:
        tabs_list.append("👥 فريق العمل والمهام الذكية")
    tabs_list.extend(["📞 العملاء والاشتراكات", "💸 تسجيل مصروف", "📦 الباقات"])
    if role == "Owner":
        tabs_list.append("📊 شيت الحسابات (المالك)")

    selected_tab = st.tabs(tabs_list)

    # --- Home Page ---
    with selected_tab[0]:
        st.title("🚀 الصفحة الرئيسية")
        c1, c2, c3 = st.columns(3)
        c1.metric("حالة النظام", "نشط 🟢")
        c2.metric("المستخدم الحالي", st.session_state.user_info["username"])
        c3.metric("الصلاحية", st.session_state.user_info["role"])

    # --- My Assigned Tasks ---
    with selected_tab[1]:
        st.title("📋 المهام الموكلة إليك")
        conn = get_db_connection()
        user_role = role
        
        if user_role != "Owner":
            tasks_df = pd.read_sql_query("SELECT * FROM assigned_tasks WHERE assigned_role = ?", conn, params=(user_role,))
        else:
            tasks_df = pd.read_sql_query("SELECT * FROM assigned_tasks", conn)

        pending = tasks_df[tasks_df["status"] == "Pending"] if not tasks_df.empty else pd.DataFrame()
        completed = tasks_df[tasks_df["status"] == "Completed ✅"] if not tasks_df.empty else pd.DataFrame()

        t1, t2 = st.tabs(["⏳ مهام قيد التنفيذ", "✅ مهام مكتملة"])
        with t1:
            if pending.empty:
                st.info("لا توجد مهام معلقة الآن! 🎉")
            else:
                for idx, row in pending.iterrows():
                    with st.expander(f"📌 العميل: {row['client_name']} — {row['task_description']}"):
                        st.write(f"**الوظيفة:** {row['assigned_role']}")
                        st.write(f"**تاريخ التكليف:** {row['created_at']}")
                        if st.button("تأكيد الإنهاء ✅", key=f"done_{row['id']}", type="primary"):
                            c = conn.cursor()
                            c.execute("UPDATE assigned_tasks SET status = 'Completed ✅', completed_at = ? WHERE id = ?",
                                      (datetime.now().strftime("%Y-%m-%d %H:%M"), row['id']))
                            conn.commit()
                            st.success("تم إكمال المهمة بنجاح!")
                            st.rerun()
        with t2:
            if not completed.empty:
                st.dataframe(completed[["client_name", "assigned_role", "task_description", "completed_at"]], use_container_width=True)
            else:
                st.caption("لا توجد مهام مكتملة بعد.")
        conn.close()

    # --- Employees & Smart Cards Layout ---
    tab_index = 2
    if role in ["Owner", "Manager"]:
        with selected_tab[tab_index]:
            st.title("👥 دليل الموظفين ومتابعة المهام الذكية")
            conn = get_db_connection()
            c = conn.cursor()

            # Popover for Adding Employees
            with st.popover("➕ إضافة موظف جديد للفريق", use_container_width=True):
                with st.form("add_emp_form"):
                    u_fullname = st.text_input("الاسم الكامل")
                    u_username = st.text_input("اسم المستخدم")
                    u_password = st.text_input("كلمة المرور", type="password")
                    u_role = st.selectbox("المسمى الوظيفي", ["Editor", "Social Media Specialist", "Web Designer", "Manager", "Owner", "Other"])
                    u_salary = st.number_input("الراتب (جنيه)", min_value=0.0)
                    if st.form_submit_button("حفظ الموظف", type="primary"):
                        try:
                            c.execute("INSERT INTO users (username, password, role, name, salary) VALUES (?, ?, ?, ?, ?)",
                                      (u_username, hash_pass(u_password), u_role, u_fullname, u_salary))
                            conn.commit()
                            st.success("تم إضافة الموظف بنجاح!")
                            st.rerun()
                        except Exception:
                            st.error("اسم المستخدم مسجل بالفعل!")

            st.write("---")
            users_df = pd.read_sql_query("SELECT id, name, username, role, salary FROM users", conn)
            all_tasks_df = pd.read_sql_query("SELECT * FROM assigned_tasks", conn)

            # Prominent Cards View for Employees
            if not users_df.empty:
                cols = st.columns(3)  # Grid of Cards
                for idx, row in users_df.iterrows():
                    with cols[idx % 3]:
                        st.markdown(f"""
                            <div class="emp-card">
                                <div class="emp-title">👤 {row['name']}</div>
                                <div class="emp-badge">{row['role']}</div>
                                <p style='margin-bottom: 5px;'><b>اسم المستخدم:</b> {row['username']}</p>
                                <p style='margin-bottom: 15px;'><b>الراتب:</b> {row['salary']:,.0f} جنيه</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Tasks related to employee role
                        emp_tasks = all_tasks_df[all_tasks_df["assigned_role"] == row['role']] if not all_tasks_df.empty else pd.DataFrame()
                        
                        with st.expander(f"📋 استعراض مهام ({row['role']}) - [{len(emp_tasks)}]"):
                            if emp_tasks.empty:
                                st.caption("لا توجد مهام موجهة لهذه الوظيفة حالياً.")
                            else:
                                for _, t_row in emp_tasks.iterrows():
                                    st.write(f"• **{t_row['client_name']}**: {t_row['task_description']} — `{t_row['status']}`")

            conn.close()
        tab_index += 1

    # --- Clients & Subscriptions ---
    with selected_tab[tab_index]:
        st.title("📞 إدارة العملاء والاشتراكات")
        conn = get_db_connection()
        c = conn.cursor()

        with st.expander("➕ إضافة عميل جديد وتوزيع المهام تلقائياً"):
            with st.form("add_client_form"):
                c_name = st.text_input("اسم العميل")
                c_phone = st.text_input("رقم الهاتف")
                
                pkgs = pd.read_sql_query("SELECT id, name, price, details FROM packages", conn)
                pkg_options = {f"{row['name']} ({row['price']:,.0f} EGP)": (row['id'], row['price'], row['details'], row['name']) for _, row in pkgs.iterrows()} if not pkgs.empty else {}
                
                selected_pkg = st.selectbox("اختر الباقة", list(pkg_options.keys()) if pkg_options else ["لا توجد باقات"])
                c_notes = st.text_area("ملاحظات")
                
                if st.form_submit_button("تسجيل العميل وتفكيك المهام", type="primary"):
                    if c_name and pkg_options:
                        pkg_id, pkg_price, pkg_details, pkg_name = pkg_options[selected_pkg]
                        current_date = datetime.now().strftime("%Y-%m-%d")
                        
                        c.execute("INSERT INTO clients (client_name, phone, package_id, notes, created_at) VALUES (?, ?, ?, ?, ?)",
                                  (c_name, c_phone, pkg_id, c_notes, current_date))
                        
                        c.execute("INSERT INTO incomes (client_name, package_name, amount, added_by) VALUES (?, ?, ?, ?)",
                                  (c_name, pkg_name, pkg_price, st.session_state.user_info["name"]))
                        
                        generated_tasks = smart_parse_package_details(pkg_details, c_name)
                        for task in generated_tasks:
                            c.execute("INSERT INTO assigned_tasks (client_name, assigned_role, task_description, created_at) VALUES (?, ?, ?, ?)", task)

                        conn.commit()
                        st.success("تم إضافة العميل وتحليل وتوزيع كافة المهام تلقائياً!")
                        st.rerun()

        clients = pd.read_sql_query('''
            SELECT c.id, c.client_name, c.phone, p.name as package, p.price, c.created_at, c.notes 
            FROM clients c LEFT JOIN packages p ON c.package_id = p.id
        ''', conn)
        st.dataframe(clients, use_container_width=True)
        conn.close()
    tab_index += 1

    # --- Log Expense ---
    with selected_tab[tab_index]:
        st.title("💸 تسجيل مصروف")
        conn = get_db_connection()
        c = conn.cursor()
        
        with st.form("exp_form"):
            e_title = st.text_input("بيان المصروف")
            e_amt = st.number_input("المبلغ (جنيه)", min_value=0.0)
            e_cat = st.selectbox("تصنيف المصروف", ["تشغيلي", "مرتبات", "تسويق", "أخرى"])
            if st.form_submit_button("حفظ المصروف", type="primary"):
                if e_title and e_amt > 0:
                    c.execute("INSERT INTO expenses (title, amount, category, added_by) VALUES (?, ?, ?, ?)",
                              (e_title, e_amt, e_cat, st.session_state.user_info["name"]))
                    conn.commit()
                    st.success("تم تسجيل المصروف بنجاح!")
        conn.close()
    tab_index += 1

    # --- Packages Hub ---
    with selected_tab[tab_index]:
        st.title("📦 الباقات والخدمات")
        conn = get_db_connection()
        c = conn.cursor()
        
        if role == "Owner":
            with st.expander("➕ إضافة باقة جديدة"):
                with st.form("add_pkg_form"):
                    p_name = st.text_input("اسم الباقة")
                    p_price = st.number_input("السعر (جنيه)", min_value=0.0)
                    p_duration = st.number_input("مدة الباقة (بالأيام)", min_value=1, value=30)
                    p_details = st.text_area("تفاصيل الباقة العامة (مثال: 30 بوست، 10 فيديوهات، تصميم موقع كامل)")
                    
                    if st.form_submit_button("حفظ الباقة", type="primary"):
                        c.execute("INSERT INTO packages (name, price, details, duration_days) VALUES (?, ?, ?, ?)",
                                  (p_name, p_price, p_details, int(p_duration)))
                        conn.commit()
                        st.success("تم حفظ الباقة بنجاح!")
                        st.rerun()

        pkgs_df = pd.read_sql_query("SELECT id, name, price, duration_days, details FROM packages", conn)
        st.dataframe(pkgs_df, use_container_width=True)
        conn.close()
    tab_index += 1

    # --- Financial Audit Sheet (Owner Only) ---
    if role == "Owner":
        with selected_tab[tab_index]:
            st.title("📊 التدقيق المالي والإيرادات")
            conn = get_db_connection()
            
            df_exp = pd.read_sql_query("SELECT * FROM expenses", conn)
            df_inc = pd.read_sql_query("SELECT * FROM incomes", conn)
            
            tot_exp = df_exp['amount'].sum() if not df_exp.empty else 0.0
            tot_inc = df_inc['amount'].sum() if not df_inc.empty else 0.0
            net = tot_inc - tot_exp
            
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي الإيرادات", f"{tot_inc:,.2f} EGP")
            c2.metric("إجمالي المصروفات", f"{tot_exp:,.2f} EGP")
            c3.metric("صافي الأرباح", f"{net:,.2f} EGP")
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_inc.to_excel(writer, index=False, sheet_name='Incomes')
                df_exp.to_excel(writer, index=False, sheet_name='Expenses')
            
            st.download_button("📥 سحب التقرير المالي (Excel)", data=output.getvalue(), file_name="audit_sheet.xlsx", use_container_width=True)
            conn.close()
