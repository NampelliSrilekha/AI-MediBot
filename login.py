# login.py

import streamlit as st
import json
from utils import init_session


USER_DB_PATH = "user_db.json"


# ------------------------------------------------------------
# LOAD / SAVE USER DATABASE
# ------------------------------------------------------------

def load_users():
    try:
        with open(USER_DB_PATH, "r") as f:
            return json.load(f)
    except:
        return {}


def save_users(data):
    with open(USER_DB_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ------------------------------------------------------------
# LOGIN PAGE
# ------------------------------------------------------------

def login_page():
    st.markdown("<h1 style='text-align:center;'>🔐 MediBot AI Login</h1>", 
                unsafe_allow_html=True)

    users = load_users()

    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", placeholder="Enter your password", type="password")

    if st.button("Login"):
        if email in users and users[email]["password"] == password:
            # Successful login
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.user_name = users[email]["name"]
            init_session()
            st.success("Login successful! Redirecting...")
            st.rerun()
        else:
            st.error("Invalid email or password.")

    st.markdown("---")

    st.subheader("Create Demo Account (Optional)")
    if st.button("Create Demo User"):
        users["demo@demo.com"] = {
            "password": "demo123",
            "name": "Demo User"
        }
        save_users(users)
        st.success("Demo user created: demo@demo.com / demo123")


# ------------------------------------------------------------
# LOGOUT FUNCTION
# ------------------------------------------------------------

def logout():
    """Clear session & logout."""
    st.session_state.clear()
    st.session_state.authenticated = False
    st.session_state.consultations = []
    st.session_state.active_consultation = None
    st.rerun()
