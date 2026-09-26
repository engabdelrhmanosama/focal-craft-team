import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. إعدادات الصفحة واللوجو ---
st.set_page_config(
    page_title="Focal Craft Team",
    page_icon="logo.jpg" if os.path.exists("logo.jpg") else "🎬",
    layout="wide"
)

# --- 2. إعداد قاعدة البيانات واسترجاعها ---
def init_db():
    if "users" not in st.session_state:
        st.session_state.users = pd.DataFrame([
            {"username": "admin", "password": "123", "role": "Owner", "name": "باشمهندس عبد الرحمن"}
        ])
    
    if "packages" not in st.session_state:
        st.session_state.packages = pd.DataFrame([
            {
                "package_name": "باقة أ", 
                "price": 5000, 
                "editor_tasks": "مونتاج 3 فيديوهات، تصميم 2 صورة", 
                "social_tasks": "كتابة 3 بوستات، جدولة النشر"
            }
        ])

    if "clients" not in st.session_state:
        st.session_state.clients = pd.DataFrame(columns=["client_name", "phone", "package", "price", "start_date"])

    if "finances" not in st.session_state:
        st.session_state.finances = pd.DataFrame(columns=["type", "amount", "category", "details", "date"])

    if "tasks" not in st.session_state:
        st.session_state.tasks = pd.DataFrame(columns=[
            "client_name", "assigned_role", "task_description", "status", "created_at", "completed_at"
        ])

init_db()

# --- 3. نظام تسجيل الدخول ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_info = None

def login_page():
    st.title("🔐 تسجيل الدخول - Focal Craft")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if os.path.exists("logo.jpg"):
            st.image("logo.jpg", width=200)
    
    with col2:
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة السر", type="password")
        if st.button("تسجيل الدخول", type="primary"):
            users = st.session_state.users
            user = users[(users["username"] == username) & (users["password"] == password)]
            if not user.empty:
                st.session_state.logged_in = True
                st.session_state.user_info = user.iloc[0].to_dict()
                st.success(f"أهلاً بك يا {st.session_state.user_info['name']}")
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة السر غير صحيحة")

if not st.session_state.logged_in:
    login_page()
    st.stop()

# --- 4. القائمة الجانبية والصلاحيات ---
current_user = st.session_state.user_info
role = current_user["role"]

st.sidebar.title(f"👤 {current_user['name']}")
st.sidebar.caption(f"الوظيفة: **{role}**")

# تحديد القوائم المتاحة لكل دور
if role == "Owner":
    menu_options = ["مهامي والشغل المطلوب", "متابعة الموظفين والمهام", "إدارة العملاء والمهام", "إدارة الباقات", "الحسابات والمالية", "إدارة الموظفين"]
elif role == "Manager":
    menu_options = ["إدارة العملاء والمهام", "متابعة الموظفين والمهام", "إدارة الباقات", "الحسابات والمالية"]
elif role in ["Editor", "Social Media Specialist"]:
    menu_options = ["مهامي والشغل المطلوب"]

choice = st.sidebar.selectbox("الانتقال إلى", menu_options)

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.logged_in = False
    st.session_state.user_info = None
    st.rerun()

# --- 5. شاشة مهامي والشغل المطلوب (للإيديتور والسوشيال ميديا والأونر) ---
if choice == "مهامي والشغل المطلوب":
    st.title("📋 قائمة المهام المطلوبة منك")
    
    # تصفية المهام بناءً على دور الموظف الحالي
    tasks_df = st.session_state.tasks
    if role != "Owner":
        my_tasks = tasks_df[tasks_df["assigned_role"] == role]
    else:
        my_tasks = tasks_df  # الأونر يرى كل شيء

    pending_tasks = my_tasks[my_tasks["status"] == "قيد التنفيذ"]
    completed_tasks = my_tasks[my_tasks["status"] == "مكتمل ✅"]

    tab1, tab2 = st.tabs(["⏳ مهام قيد التنفيذ", "✅ مهام تم إنجازها"])

    with tab1:
        if pending_tasks.empty:
            st.info("لا يوجد مهام معلقة لديك حالياً! 👏")
        else:
            for idx, row in pending_tasks.iterrows():
                with st.expander(f"📌 عميل: {row['client_name']} - {row['task_description']}"):
                    st.write(f"**المطلوب:** {row['task_description']}")
                    st.write(f"**الموجه لـ:** {row['assigned_role']}")
                    st.write(f"**تاريخ الإضافة:** {row['created_at']}")
                    
                    if st.button("تحديد كـ مكتمل ✅", key=f"done_{idx}"):
                        st.session_state.tasks.at[idx, "status"] = "مكتمل ✅"
                        st.session_state.tasks.at[idx, "completed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        st.success("عاش! تم تحديث حالة التاسك.")
                        st.rerun()

    with tab2:
        if completed_tasks.empty:
            st.caption("لم تقم بإنجاز مهام بعد.")
        else:
            st.dataframe(completed_tasks[["client_name", "task_description", "completed_at"]], use_container_width=True)

# --- 6. شاشة متابعة الموظفين والمهام (للأونر والمدير) ---
elif choice == "متابعة الموظفين والمهام":
    st.title("📊 لوحة متابعة إنجاز الموظفين")
    
    tasks_df = st.session_state.tasks
    if tasks_df.empty:
        st.info("لا توجد مهام مسجلة في النظام بعد.")
    else:
        col1, col2, col3 = st.columns(3)
        total_tasks = len(tasks_df)
        done_tasks = len(tasks_df[tasks_df["status"] == "مكتمل ✅"])
        pending = total_tasks - done_tasks

        col1.metric("إجمالي المهام", total_tasks)
        col2.metric("المهام المكتملة ✅", done_tasks)
        col3.metric("المهام المتبقية ⏳", pending)

        st.divider()
        st.subheader("📌 تقرير الإنجاز حسب القسم")
        
        roles = ["Editor", "Social Media Specialist"]
        for r in roles:
            r_tasks = tasks_df[tasks_df["assigned_role"] == r]
            st.markdown(f"### قسم: **{r}**")
            if r_tasks.empty:
                st.caption("لا توجد مهام لهذا القسم.")
            else:
                st.dataframe(r_tasks[["client_name", "task_description", "status", "created_at", "completed_at"]], use_container_width=True)

# --- 7. إدارة العملاء والمهام ---
elif choice == "إدارة العملاء والمهام":
    st.title("👥 إدارة العملاء وتوزيع المهام")
    
    with st.form("add_client"):
        st.subheader("إضافة عميل جديد وتشغيل باقته")
        c_name = st.text_input("اسم العميل")
        c_phone = st.text_input("رقم الهاتف")
        
        pkg_names = st.session_state.packages["package_name"].tolist() if not st.session_state.packages.empty else []
        selected_pkg = st.selectbox("اختر الباقة", pkg_names)
        
        submit = st.form_submit_button("إضافة العميل وتوليد المهام")
        
        if submit and c_name and selected_pkg:
            pkg_data = st.session_state.packages[st.session_state.packages["package_name"] == selected_pkg].iloc[0]
            price = pkg_data["price"]
            
            # 1. إضافة العميل
            new_client = pd.DataFrame([{"client_name": c_name, "phone": c_phone, "package": selected_pkg, "price": price, "start_date": datetime.now().strftime("%Y-%m-%d")}])
            st.session_state.clients = pd.concat([st.session_state.clients, new_client], ignore_index=True)
            
            # 2. إضافة إيراد مالي
            new_rev = pd.DataFrame([{"type": "إيراد", "amount": price, "category": "اشتراك عميل", "details": f"عميل: {c_name} - {selected_pkg}", "date": datetime.now().strftime("%Y-%m-%d")}])
            st.session_state.finances = pd.concat([st.session_state.finances, new_rev], ignore_index=True)
            
            # 3. توليد مهام للإيديتور والسوشيال ميديا تلقائياً
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_tasks = []
            
            if pkg_data["editor_tasks"]:
                new_tasks.append({
                    "client_name": c_name, "assigned_role": "Editor", 
                    "task_description": pkg_data["editor_tasks"], "status": "قيد التنفيذ", 
                    "created_at": now_str, "completed_at": "-"
                })
            if pkg_data["social_tasks"]:
                new_tasks.append({
                    "client_name": c_name, "assigned_role": "Social Media Specialist", 
                    "task_description": pkg_data["social_tasks"], "status": "قيد التنفيذ", 
                    "created_at": now_str, "completed_at": "-"
                })
            
            st.session_state.tasks = pd.concat([st.session_state.tasks, pd.DataFrame(new_tasks)], ignore_index=True)
            st.success("تمت إضافة العميل وتلقائياً تم تحويل المهام للمونتير ومسؤول السوشيال ميديا! 🚀")

    st.divider()
    st.subheader("قائمة العملاء الحالية")
    st.dataframe(st.session_state.clients, use_container_width=True)

# --- 8. إدارة الباقات ---
elif choice == "إدارة الباقات":
    st.title("📦 إدارة الباقات والخطط")
    
    with st.form("add_package"):
        p_name = st.text_input("اسم الباقة (مثلاً: باقة أ)")
        p_price = st.number_input("سعر الباقة (جنيه)", min_value=0)
        e_tasks = st.text_area("مهام الإيديتور/المونتير في هذه الباقة (مثلاً: 3 فيديوهات وصورة)")
        s_tasks = st.text_area("مهام مسؤول السوشيال ميديا (مثلاً: كتابة 3 بوستات ونشرها)")
        
        if st.form_submit_button("حفظ الباقة"):
            if p_name:
                new_pkg = pd.DataFrame([{"package_name": p_name, "price": p_price, "editor_tasks": e_tasks, "social_tasks": s_tasks}])
                st.session_state.packages = pd.concat([st.session_state.packages, new_pkg], ignore_index=True)
                st.success("تمت إضافة الباقة بنجاح!")
                st.rerun()

    st.subheader("الباقات المتاحة")
    st.dataframe(st.session_state.packages, use_container_width=True)

# --- 9. الحسابات والمالية ---
elif choice == "الحسابات والمالية":
    st.title("💰 المالية والحسابات - Focal Craft")
    
    fin_df = st.session_state.finances
    total_rev = fin_df[fin_df["type"] == "إيراد"]["amount"].sum()
    total_exp = fin_df[fin_df["type"] == "مصروف"]["amount"].sum()
    net_profit = total_rev - total_exp

    col1, col2, col3 = st.columns(3)
    col1.metric("إجمالي الإيرادات", f"{total_rev:,} ج.م")
    col2.metric("إجمالي المصروفات", f"{total_exp:,} ج.م")
    col3.metric("صافي الأرباح", f"{net_profit:,} ج.م")

    st.divider()
    st.subheader("سجل العمليات المالية")
    st.dataframe(fin_df, use_container_width=True)

# --- 10. إدارة الموظفين ---
elif choice == "إدارة الموظفين":
    st.title("👥 إدارة فريق العمل والوظائف")
    
    with st.form("add_user"):
        u_name = st.text_input("اسم الموظف")
        u_user = st.text_input("اسم المستخدم (Username)")
        u_pass = st.text_input("كلمة السر", type="password")
        u_role = st.selectbox("المسمى الوظيفي / الدور", [
            "Owner", 
            "Manager", 
            "Editor", 
            "Social Media Specialist"
        ])
        
        if st.form_submit_button("إضافة الموظف"):
            if u_user and u_pass:
                new_u = pd.DataFrame([{"username": u_user, "password": u_pass, "role": u_role, "name": u_name}])
                st.session_state.users = pd.concat([st.session_state.users, new_u], ignore_index=True)
                st.success("تم إضافة الموظف بنجاح!")
                st.rerun()

    st.subheader("فريق العمل الحالي")
    st.dataframe(st.session_state.users[["name", "username", "role"]], use_container_width=True)
