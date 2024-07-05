import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, db
import warnings

# Hide warnings
warnings.filterwarnings("ignore")

# Hide Streamlit warnings with CSS
hide_st_style = """
            <style>
            .stAlert {display: none;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(r'openmind-6c55b-firebase-adminsdk-emz7g-177d018c8c.json')
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://openmind-6c55b-default-rtdb.firebaseio.com/'
    })

# User dictionary for authentication
users = {
    "admin": {"password": "admin_password", "name": "Manish"},
    "employee1": {"name": "Bharat", "password": "password1", "phone": "phone_number1"},
    "employee2": {"name": "Employee2", "password": "password2", "phone": "phone_number2"},
    # Add other employees here
}

# Authentication function
def authenticate(username, password):
    if username in users and users[username]['password'] == password:
        return username
    else:
        return None

# Initialize session state variables
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Sidebar for login
st.sidebar.image("OpenmindLogo.png")

if st.session_state.user_role is None:
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login_button = st.sidebar.button("Login")

    if login_button:
        user_role = authenticate(username, password)
        if user_role:
            st.session_state.user_role = user_role
            st.session_state.username = username
            st.experimental_set_query_params(user=user_role)
            st.sidebar.write(f"Welcome {username}")
        else:
            st.sidebar.write("Invalid credentials")
else:
    st.sidebar.write(f"Logged in as {st.session_state.user_role}")
    if st.sidebar.button("Logout"):
        st.session_state.user_role = None
        st.session_state.username = None
        st.experimental_set_query_params()  # Clear query params
        st.experimental_rerun()

# Check if user is logged in
if st.session_state.user_role:
    user_role = st.session_state.user_role
    username = st.session_state.username

    # Admin Interface: Options
    if user_role == "admin":
        st.header("Admin Dashboard")

        current_time = datetime.now().strftime("%H:%M")
        st.subheader(f"Hi {users[username]['name']}, it's {current_time}. Have a Nice Day!")

        admin_option = st.sidebar.selectbox("Select Action", ["Add Task", "View Tasks", "Delete Tasks"], key="admin_action_select")

        # Add Task
        if admin_option == "Add Task":
            st.subheader("Assign Task")
            employees = st.multiselect("Select Employee(s)", [user for user in users.keys() if user != "admin"], key="admin_select_employees")
            task = st.text_area("Task Description")
            deadline_date = st.date_input("Deadline Date")
            deadline_time = st.time_input("Deadline Time")

            if st.button("Assign Task"):
                deadline = datetime.combine(deadline_date, deadline_time)
                task_ref = db.reference('tasks')
                for employee in employees:
                    new_task_ref = task_ref.push({
                        'employee': employee,
                        'task': task,
                        'deadline': deadline.isoformat(),
                        'status': 'Pending',
                        'assigned_time': datetime.now().isoformat()
                    })
                st.write("Task assigned successfully!")

        # View Tasks
        elif admin_option == "View Tasks":
            st.subheader("View Tasks")
            task_ref = db.reference('tasks')
            tasks = task_ref.get()
            if tasks:
                task_list = []
                for count, (task_key, task_value) in enumerate(tasks.items(), 1):
                    task_list.append({
                        "Count": count,
                        "Employee": task_value['employee'],
                        "Description": task_value['task'],
                        "Deadline": task_value['deadline'].replace('T', ' '),
                        "Status": task_value['status'],
                        "Key": task_key
                    })
                
                task_df = pd.DataFrame(task_list)
                st.write(task_df[["Count", "Employee", "Description", "Deadline", "Status"]].to_html(index=False), unsafe_allow_html=True)

        # Delete Tasks
        elif admin_option == "Delete Tasks":
            st.subheader("Delete Tasks")
            task_ref = db.reference('tasks')
            tasks = task_ref.get()
            if tasks:
                task_list = []
                for count, (task_key, task_value) in enumerate(tasks.items(), 1):
                    task_list.append({
                        "Count": count,
                        "Employee": task_value['employee'],
                        "Description": task_value['task'],
                        "Deadline": task_value['deadline'].replace('T', ' '),
                        "Status": task_value['status'],
                        "Key": task_key
                    })
                
                task_df = pd.DataFrame(task_list)
                st.write(task_df[["Count", "Employee", "Description", "Deadline", "Status"]].to_html(index=False), unsafe_allow_html=True)

                delete_task_key = st.text_input("Enter the Task Count to Delete")
                if st.button("Delete Task"):
                    if delete_task_key.isdigit():
                        delete_task_key = int(delete_task_key) - 1
                        if 0 <= delete_task_key < len(task_list):
                            task_to_delete = task_list[delete_task_key]["Key"]
                            task_ref.child(task_to_delete).delete()
                            st.write("Task deleted successfully")
                            st.experimental_rerun()
                        else:
                            st.error("Invalid Task Count")
                    else:
                        st.error("Please enter a valid Task Count")

    # Employee Interface: View and Update Tasks
    elif user_role and user_role != "admin":
        st.title("Openmind Design Inc")
        current_time_container = st.empty()

        current_time = datetime.now().strftime("%H:%M")
        st.subheader(f"Hi {users[username]['name']}, it's {current_time}")

        st.header("My Tasks")
        task_ref = db.reference('tasks')
        tasks = task_ref.order_by_child('employee').equal_to(user_role).get()
        count = 1

        for task_key, task_value in tasks.items():
            st.subheader(f"Task {count}")
            st.write(f"Description: {task_value['task']}")
            st.write(f"Deadline: {task_value['deadline'].replace('T', ' ')}")
            status = st.selectbox(
                "Status", 
                ["Pending", "Doing", "Completed"], 
                index=["Pending", "Doing", "Completed"].index(task_value['status']),
                key=f"status_{task_key}"
            )
            count += 1

            if st.button(f"Update Status", key=f"update_status_{task_key}"):
                task_ref.child(task_key).update({'status': status})
                st.success("Status updated successfully")

    # Check for overdue tasks and tasks completed for more than 36 hours
    task_ref = db.reference('tasks')
    all_tasks = task_ref.get()

    try:
        for task_key, task_value in all_tasks.items():
            if task_value['status'] != 'Completed' and datetime.fromisoformat(task_value['deadline']) < datetime.now():
                employee = task_value['employee']
                if user_role == employee:
                    st.components.v1.html(f"""
                        <script>
                        alert('Task "{task_value['task']}" is overdue!');
                        </script>
                    """, height=0)

            elif task_value['status'] == 'Completed':
                completion_time = datetime.fromisoformat(task_value['assigned_time'])
                if datetime.now() - completion_time > timedelta(hours=36):
                    task_ref.child(task_key).delete()
    except AttributeError:
        pass
else:
    st.sidebar.warning("Please log in to view the task management system.")
