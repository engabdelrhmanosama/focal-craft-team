import streamlit as st
from PIL import Image

# تحميل صورة اللوجو
logo = Image.open("logo.jpg")

# ضبط إعدادات الصفحة (اسم التطبيق والأيقونة)
st.set_page_config(
    page_title="فوكال كرافت تيم",  # الاسم الذي يظهر في تبويب المتصفح ومن الخارج
    page_icon=logo,              # أيقونة اللوجو (Favicon)
    layout="wide"
)

# عرض اللوجو والعنوان داخل الصفحة
st.image(logo, width=150)
st.title("Focal Craft Team")

import streamlit as st
import pandas as pd
import sqlite3
import hashlib
from datetime import datetime
import os
import base64

# --- 1. SETTINGS & PAGE CONFIG ---
st.set_page_config(
    page_title="Focal Craft Team",
    page_icon="🎨",
    layout="wide"
)

# Helper function for image base64
def get_image_base64(image_path):
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

logo_file = "logo.jpg" if os.path.exists("logo.jpg") else ("logo.jpg" if os.path.exists("logo.jpg") else ("logo.png" if os.path.exists("logo.png") else ""))
logo_base64 = get_image_base64(logo_file)

# --- 2. DATABASE SETUP ---
conn = sqlite3.connect("focal_craft.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price REAL,
    services TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    package_id INTEGER,
    start_date TEXT,
    completed_services TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    amount REAL,
    date TEXT,
    added_by TEXT
)
''')
conn.commit()

# Default admin setup
def hash_pass(password):
    return hashlib.sha256(password.encode()).hexdigest()

cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users VALUES ('admin', ?, 'owner')", (hash_pass("admin123"),))
    conn.commit()

# Session State Setup
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

# --- 3. CUSTOM STYLING ---
if not st.session_state.logged_in:
    bg_style = f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.85)), 
                    url("data:image/png;base64,{logo_base64}") no-repeat center center fixed;
        background-size: cover;
    }}
    .login-card {{
        background: rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        padding: 40px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        text-align: center;
        margin-top: 20px;
    }}
    .login-card h1 {{
        color: #ffffff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 700;
        margin-top: 15px;
        margin-bottom: 5px;
        letter-spacing: 1.5px;
    }}
    .login-card p {{
        color: #cbd5e1;
        font-size: 14px;
        letter-spacing: 2px;
        margin-bottom: 25px;
    }}
    </style>
    """
    st.markdown(bg_style, unsafe_allow_html=True)

# --- 4. LOGIN / AUTHENTICATION ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        
        if logo_file:
            st.image(logo_file, width=130)
            
        st.markdown("""
            <h1>FOCAL CRAFT</h1>
            <p>MEDIA PRODUCTION TEAM</p>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("Sign In")
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True):
            hashed = hash_pass(password_input)
            cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username_input, hashed))
            user = cursor.fetchone()
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.session_state.role = user[0]
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    st.stop()

# --- 5. DASHBOARD MAIN APP ---
if logo_file:
    st.sidebar.image(logo_file, width=140)

st.sidebar.title(f"Welcome, {st.session_state.username.capitalize()}")
st.sidebar.caption(f"Role: **{st.session_state.role.upper()}**")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

col_h1, col_h2 = st.columns([0.1, 0.9])
with col_h1:
    if logo_file:
        st.image(logo_file, width=60)
with col_h2:
    st.markdown("<h2 style='margin-top: 10px;'>Focal Craft Team Workspace</h2>", unsafe_allow_html=True)

st.divider()

# Navigation
menu_options = ["Add Client", "Client Services Tracker", "Record Expenses"]
if st.session_state.role == "owner":
    menu_options.extend(["Manage Packages", "Monthly Financial Sheet", "User Management"])

choice = st.sidebar.radio("Navigation Menu", menu_options)

# --- 6. MENU ACTIONS ---

# A. ADD CLIENT
if choice == "Add Client":
    st.header("Register New Client")
    cursor.execute("SELECT id, name, price FROM packages")
    packages = cursor.fetchall()
    
    if not packages:
        st.warning("No media packages available yet. Please ask Owner to create packages.")
    else:
        pkg_dict = {f"{p[1]} (${p[2]})": p[0] for p in packages}
        
        with st.form("client_form"):
            client_name = st.text_input("Client Name")
            client_phone = st.text_input("Phone Number")
            selected_pkg_name = st.selectbox("Select Package", list(pkg_dict.keys()))
            submit = st.form_submit_button("Add Client")
            
            if submit:
                if client_name and client_phone:
                    pkg_id = pkg_dict[selected_pkg_name]
                    today = datetime.now().strftime("%Y-%m-%d")
                    cursor.execute("INSERT INTO clients (name, phone, package_id, start_date, completed_services) VALUES (?, ?, ?, ?, ?)",
                                   (client_name, client_phone, pkg_id, today, ""))
                    conn.commit()
                    st.success(f"Client {client_name} added successfully!")
                else:
                    st.error("Please fill in all fields.")

# B. CLIENT SERVICES TRACKER
elif choice == "Client Services Tracker":
    st.header("Active Clients & Service Progress")
    cursor.execute("""
        SELECT c.id, c.name, c.phone, p.name, p.services, c.start_date, c.completed_services, p.price 
        FROM clients c 
        JOIN packages p ON c.package_id = p.id
    """)
    clients = cursor.fetchall()
    
    for client in clients:
        c_id, c_name, c_phone, p_name, p_services, start_date, completed_str, p_price = client
        completed_list = completed_str.split(",") if completed_str else []
        all_services = [s.strip() for s in p_services.split(",") if s.strip()]
        
        with st.expander(f"📌 {c_name} | Package: {p_name} | Phone: {c_phone}"):
            st.write(f"**Subscription Date:** {start_date} *(Valid for 1 Month)*")
            
            updated_completed = []
            for idx, service in enumerate(all_services):
                is_checked = service in completed_list
                checked = st.checkbox(service, value=is_checked, key=f"{c_id}_{idx}")
                if checked:
                    updated_completed.append(service)
            
            if st.button("Save Progress", key=f"save_{c_id}"):
                new_completed_str = ",".join(updated_completed)
                cursor.execute("UPDATE clients SET completed_services=? WHERE id=?", (new_completed_str, c_id))
                conn.commit()
                st.success("Progress saved!")

            if st.session_state.role == "owner":
                st.divider()
                if st.button(f"🗑️ Delete Client: {c_name}", key=f"del_{c_id}"):
                    cursor.execute("DELETE FROM clients WHERE id=?", (c_id,))
                    conn.commit()
                    st.rerun()

# C. RECORD EXPENSES
elif choice == "Record Expenses":
    st.header("Record Company Expense")
    with st.form("expense_form"):
        title = st.text_input("Expense Description")
        amount = st.number_input("Amount ($)", min_value=0.0, step=1.0)
        submit = st.form_submit_button("Record Expense")
        
        if submit and title and amount > 0:
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("INSERT INTO expenses (title, amount, date, added_by) VALUES (?, ?, ?, ?)",
                           (title, amount, today, st.session_state.username))
            conn.commit()
            st.success("Expense recorded successfully!")

# D. MANAGE PACKAGES (Owner Only - Complete CRUD)
elif choice == "Manage Packages" and st.session_state.role == "owner":
    st.header("Media Packages Management")
    
    # Create Package
    with st.expander("➕ Create New Package"):
        with st.form("package_form"):
            pkg_name = st.text_input("Package Name")
            pkg_price = st.number_input("Price ($)", min_value=0.0, step=10.0)
            pkg_services = st.text_area("Services (Separate with commas ',')")
            submit = st.form_submit_button("Save Package")
            
            if submit and pkg_name and pkg_services:
                cursor.execute("INSERT INTO packages (name, price, services) VALUES (?, ?, ?)",
                               (pkg_name, pkg_price, pkg_services))
                conn.commit()
                st.success(f"Package '{pkg_name}' created!")
                st.rerun()

    # Edit / Delete Packages
    st.subheader("Existing Packages")
    cursor.execute("SELECT * FROM packages")
    pkgs = cursor.fetchall()
    
    if pkgs:
        for p in pkgs:
            p_id, p_name, p_price, p_services = p
            with st.expander(f"📦 {p_name} - ${p_price}"):
                with st.form(key=f"edit_pkg_{p_id}"):
                    edit_name = st.text_input("Package Name", value=p_name)
                    edit_price = st.number_input("Price ($)", value=float(p_price), step=10.0)
                    edit_services = st.text_area("Services (Comma Separated)", value=p_services)
                    
                    col_b1, col_b2 = st.columns(2)
                    save_changes = col_b1.form_submit_button("💾 Save Changes")
                    
                    if save_changes:
                        cursor.execute("UPDATE packages SET name=?, price=?, services=? WHERE id=?", 
                                       (edit_name, edit_price, edit_services, p_id))
                        conn.commit()
                        st.success("Package updated successfully!")
                        st.rerun()

                if st.button(f"🗑️ Delete Package '{p_name}'", key=f"del_pkg_{p_id}"):
                    cursor.execute("DELETE FROM packages WHERE id=?", (p_id,))
                    conn.commit()
                    st.success("Package deleted!")
                    st.rerun()

# E. FINANCIAL SHEET (Owner Only)
elif choice == "Monthly Financial Sheet" and st.session_state.role == "owner":
    st.header("📈 Financial Report (Owner View)")
    cursor.execute("SELECT SUM(p.price) FROM clients c JOIN packages p ON c.package_id = p.id")
    total_income = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_expenses = cursor.fetchone()[0] or 0.0
    
    net_profit = total_income - total_expenses
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"${total_income:,.2f}")
    col2.metric("Total Expenses", f"${total_expenses:,.2f}")
    col3.metric("Net Profit", f"${net_profit:,.2f}")
    
    st.divider()
    st.subheader("Detailed Expenses Log")
    cursor.execute("SELECT title, amount, date, added_by FROM expenses")
    exp_data = cursor.fetchall()
    if exp_data:
        df_exp = pd.DataFrame(exp_data, columns=["Description", "Amount ($)", "Date", "Added By"])
        st.dataframe(df_exp, use_container_width=True)

# F. USER MANAGEMENT (Owner Only - Complete Management)
elif choice == "User Management" and st.session_state.role == "owner":
    st.header("👥 System Users Management")
    
    # 1. View & Delete Users
    st.subheader("Current Registered Users")
    cursor.execute("SELECT username, role FROM users")
    users = cursor.fetchall()
    
    if users:
        df_users = pd.DataFrame(users, columns=["Username", "Role"])
        st.dataframe(df_users, use_container_width=True)
        
        st.write("---")
        st.subheader("🗑️ Delete a User")
        user_list = [u[0] for u in users if u[0] != "admin"] # Prevent deleting main admin
        if user_list:
            user_to_delete = st.selectbox("Select User to Remove", user_list)
            if st.button(f"Delete Account '{user_to_delete}'"):
                cursor.execute("DELETE FROM users WHERE username=?", (user_to_delete,))
                conn.commit()
                st.success(f"User '{user_to_delete}' has been deleted!")
                st.rerun()
        else:
            st.info("No employee accounts available to delete.")

    st.write("---")
    
    # 2. Add New User
    with st.expander("➕ Create New User"):
        new_user = st.text_input("New Username")
        new_pass = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["employee", "owner"])
        if st.button("Create User"):
            if new_user and new_pass:
                try:
                    cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (new_user, hash_pass(new_pass), new_role))
                    conn.commit()
                    st.success(f"User '{new_user}' created successfully!")
                    st.rerun()
                except:
                    st.error("Username already exists!")
            else:
                st.error("Please fill in all fields.")

    # 3. Reset Password
    with st.expander("🔑 Reset User Password"):
        cursor.execute("SELECT username FROM users")
        all_users = [u[0] for u in cursor.fetchall()]
        selected_user = st.selectbox("Select User to Change Password", all_users)
        reset_pass = st.text_input("New Password", type="password", key="reset_p")
        if st.button("Update Password"):
            if reset_pass:
                cursor.execute("UPDATE users SET password=? WHERE username=?", (hash_pass(reset_pass), selected_user))
                conn.commit()
                st.success(f"Password updated for '{selected_user}'!")
