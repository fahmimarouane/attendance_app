import streamlit as st
import json
import hashlib
from pathlib import Path

class AuthManager:
    def __init__(self):
        self.users_file = "users.json"
        self.initialize_users_file()
        
    def initialize_users_file(self):
        """Initialize users file with admin if it doesn't exist"""
        if not Path(self.users_file).exists():
            admin_password = self.hash_password("admin123")  # Default admin password
            initial_users = {
                "admin": {
                    "password": admin_password,
                    "role": "admin",
                    "name": "Administrator"
                }
            }
            self.save_users(initial_users)
    
    @staticmethod
    def hash_password(password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def load_users(self):
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def save_users(self, users):
        """Save users to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=4)
    
    def add_teacher(self, username, access_code, name):
        """Add a new teacher account"""
        users = self.load_users()
        if username in users:
            return False, "Username already exists"
        
        users[username] = {
            "password": self.hash_password(access_code),
            "role": "teacher",
            "name": name
        }
        self.save_users(users)
        return True, "Teacher added successfully"
    
    def remove_teacher(self, username):
        """Remove a teacher account"""
        users = self.load_users()
        if username not in users or users[username]["role"] == "admin":
            return False, "Invalid username or cannot remove admin"
        
        del users[username]
        self.save_users(users)
        return True, "Teacher removed successfully"
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        users = self.load_users()
        if username not in users:
            return False, None
        
        if users[username]["password"] == self.hash_password(password):
            return True, users[username]
        return False, None

def show_login():
    """Display login form"""
    st.title("🔐 Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        auth_manager = AuthManager()
        success, user = auth_manager.verify_user(username, password)
        
        if success:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.session_state["user_role"] = user["role"]
            st.session_state["user_name"] = user["name"]
            st.success(f"Welcome {user['name']}!")
            st.rerun()
        else:
            st.error("Invalid username or password")

def show_user_management():
    """Display user management interface for admin"""
    st.subheader("👥 User Management")
    
    auth_manager = AuthManager()
    
    # Add new teacher
    st.write("### Add New Teacher")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_username = st.text_input("Username")
    with col2:
        new_access_code = st.text_input("Access Code", type="password")
    with col3:
        teacher_name = st.text_input("Teacher Name")
    
    if st.button("Add Teacher"):
        if new_username and new_access_code and teacher_name:
            success, message = auth_manager.add_teacher(new_username, new_access_code, teacher_name)
            if success:
                st.success(message)
            else:
                st.error(message)
        else:
            st.warning("Please fill all fields")
    
    # List and manage existing teachers
    st.write("### Existing Teachers")
    users = auth_manager.load_users()
    teachers = {username: data for username, data in users.items() 
               if data["role"] == "teacher"}
    
    if teachers:
        for username, data in teachers.items():
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Username:** {username}")
            with col2:
                st.write(f"**Name:** {data['name']}")
            with col3:
                if st.button("Remove", key=f"remove_{username}"):
                    success, message = auth_manager.remove_teacher(username)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    else:
        st.info("No teachers added yet")

def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get("authenticated", False)

def logout():
    """Log out user"""
    if st.sidebar.button("Logout"):
        for key in ["authenticated", "username", "user_role", "user_name"]:
            st.session_state.pop(key, None)
        st.rerun()
