# utils.py
import streamlit as st
from datetime import datetime
from PIL import Image
import base64
from io import BytesIO


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def init_session():
    if "consultations" not in st.session_state:
        st.session_state.consultations = []
    if "active_consultation" not in st.session_state:
        st.session_state.active_consultation = None
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_name" not in st.session_state:
        st.session_state.user_name = None
    if "user_email" not in st.session_state:
        st.session_state.user_email = None


# ---------------------------
# MESSAGE CLASSIFICATION
# ---------------------------

def classify_user(text):
    t = text.lower()
    if "remedy" in t or "help" in t or "what should" in t:
        return "user_followup"
    if t.endswith("?"):
        return "user_question"
    if "skin" in t or "issue" in t or "problem" in t:
        return "user_description"
    return "user_message"


def classify_ai(text):
    t = text.lower()
    if any(w in t for w in ["apply", "use", "avoid", "moistur", "cream"]):
        return "ai_remedy"
    if any(w in t for w in ["looks", "appears", "seems"]):
        return "ai_observation"
    return "ai_response"


def add_message(consultation, role: str, content: str):
    # 🔐 Ensure we always have a messages list so nothing is lost
    if "messages" not in consultation or consultation["messages"] is None:
        consultation["messages"] = []

    msg_type = classify_user(content) if role == "user" else classify_ai(content)

    consultation["messages"].append(
        {
            "role": role,
            "content": content,
            "type": msg_type,
            "timestamp": now_str(),
        }
    )
    consultation["updated_at"] = datetime.now()


def load_image(uploaded_file):
    try:
        return Image.open(uploaded_file).convert("RGB")
    except Exception:
        return None


def get_active_consultation():
    idx = st.session_state.get("active_consultation")
    if idx is None:
        return None
    if idx < 0 or idx >= len(st.session_state.consultations):
        return None
    return st.session_state.consultations[idx]


def save_active_consultation(consultation):
    idx = st.session_state.active_consultation
    if idx is not None:
        st.session_state.consultations[idx] = consultation
