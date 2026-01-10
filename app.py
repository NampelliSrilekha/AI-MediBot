import streamlit as st
from io import BytesIO
from PIL import Image

from styles import load_css
from login import login_page, logout
from utils import (
    init_session,
    get_active_consultation,
    save_active_consultation,
    add_message,
)
from consultations import render_consultation_sidebar, create_new_consultation
from onboarding import (
    handle_onboarding,
    render_skin_type_buttons,
    render_problem_type_buttons,
)
from detector import CLIPSkinDetector
from llm import explain_with_groq


# ------------------------------------------------------------
# HELPER: sanitize LLM output (remove all "*")
# ------------------------------------------------------------
def sanitize_llm_output(text: str) -> str:
    if not isinstance(text, str):
        return text
    return text.replace("*", "")


# ------------------------------------------------------------
# PAGE CONFIG & GLOBAL CSS
# ------------------------------------------------------------
st.set_page_config(
    page_title="MediBot AI",
    page_icon="🩺",
    layout="wide",
)
st.markdown(load_css(), unsafe_allow_html=True)


# ------------------------------------------------------------
# AUTH CHECK
# ------------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    login_page()
    st.stop()


# ------------------------------------------------------------
# SESSION INIT
# ------------------------------------------------------------
init_session()

# Cache CLIP model so we don't reload it every request
if "clip_detector" not in st.session_state:
    st.session_state.clip_detector = CLIPSkinDetector()
detector = st.session_state.clip_detector


# ------------------------------------------------------------
# SIDEBAR: user info + consultations + logout
# ------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"<div class='sidebar-title'>👤 Welcome, {st.session_state.user_name}</div>",
        unsafe_allow_html=True,
    )

    if st.button("🚪 Logout"):
        logout()
        st.rerun()

    st.markdown("---")
    render_consultation_sidebar()

    if st.button("➕ Start New Consultation", key="new_consult_btn"):
        create_new_consultation()
        st.rerun()


# Ensure there is at least one consultation
if not st.session_state.consultations:
    create_new_consultation()

consultation = get_active_consultation()
if consultation is None:
    st.error("No consultation selected.")
    st.stop()


# ------------------------------------------------------------
# CHAT HISTORY RENDERER (TEXT + OPTIONAL IMAGE)
# ------------------------------------------------------------
def display_chat_history():
    for msg in consultation["messages"]:
        css_class = "assistant" if msg["role"] == "assistant" else "user"
        who = "MediBot AI" if msg["role"] == "assistant" else "You"

        st.markdown(
            f"""
            <div class="chat-message {css_class}">
                <strong>{who}</strong><br>
                {msg["content"]}<br>
                <div class="chat-timestamp">{msg["timestamp"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # If this message has an image, show it directly under the bubble
        if "image_bytes" in msg and msg["image_bytes"]:
            st.image(
                msg["image_bytes"],
                caption="Uploaded image",
                use_container_width=False,
                width=220,
            )


# ------------------------------------------------------------
# PAGE HEADER
# ------------------------------------------------------------
st.markdown(
    "<h1 style='text-align:center;'>🩺 MediBot AI Consultation</h1>",
    unsafe_allow_html=True,
)
st.markdown("---")


# ============================================================
# ONBOARDING MODE
# ============================================================

if consultation.get("onboarding_step", 1) != 999:
    # If step == 1 and no messages, send greeting once
    if consultation["onboarding_step"] == 1 and not consultation["messages"]:
        handle_onboarding(consultation, None)
        save_active_consultation(consultation)

    # Show onboarding chat so far
    display_chat_history()

    step = consultation["onboarding_step"]

    button_choice = None
    if step == 4:
        st.markdown("### Choose your skin type:")
        button_choice = render_skin_type_buttons()
    elif step == 5:
        st.markdown("### Choose the type of skin issue:")
        button_choice = render_problem_type_buttons()

    # Chat-style answer box
    user_input = st.chat_input("Type your answer here...")

    # If user clicked button but didn't type text, use button value
    if user_input is None and button_choice is not None:
        user_input = button_choice

    if user_input is not None:
        # store user onboarding answer as message
        add_message(consultation, "user", user_input)

        # advance onboarding logic
        _ = handle_onboarding(consultation, user_input)
        save_active_consultation(consultation)

        st.rerun()

    # still onboarding → don't show main chat yet
    st.stop()


# ============================================================
# NORMAL CHAT MODE (after onboarding finished)
# ============================================================

# 1) Show chat history once
display_chat_history()
st.markdown("---")

# Ensure a place in session for pending image bytes + uploader revision
if "pending_image_bytes" not in st.session_state:
    st.session_state["pending_image_bytes"] = None
if "uploader_rev" not in st.session_state:
    st.session_state["uploader_rev"] = 0

# 2) Composer row: image upload + chat input
col1, col2 = st.columns([1, 3])

with col1:
    uploader_key = f"chat_image_uploader_{st.session_state['uploader_rev']}"
    uploaded_file = st.file_uploader(
        "Attach an image (optional)",
        type=["png", "jpg", "jpeg"],
        key=uploader_key,
    )
    if uploaded_file is not None:
        # store bytes only; no preview here
        st.session_state["pending_image_bytes"] = uploaded_file.getvalue()

with col2:
    user_input = st.chat_input("Describe your skin concern or ask a question...")


# ------------------------------------------------------------
# 3) MESSAGE PROCESSING (image goes into chat, uploader reset via key bump)
# ------------------------------------------------------------
if user_input is not None:
    # Grab any pending image bytes (if user selected one)
    image_bytes = st.session_state.get("pending_image_bytes")
    pil_image = None
    if image_bytes:
        pil_image = Image.open(BytesIO(image_bytes)).convert("RGB")

    # Store user message
    add_message(consultation, "user", user_input)

    # Attach image bytes to the *last* message if present
    if image_bytes:
        consultation["messages"][-1]["image_bytes"] = image_bytes

    # Generate response with spinner
    spinner_text = (
        "Analyzing your skin image..."
        if pil_image is not None
        else "Thinking about your skin concern..."
    )

    with st.spinner(spinner_text):
        if pil_image is not None:
            description = user_input.strip() or "No description provided."
            predictions = detector.predict(image=pil_image, top_k=3)
            explanation = explain_with_groq(
                predictions=predictions,
                user_description=description,
                consultation=consultation,
            )
        else:
            explanation = explain_with_groq(
                predictions=[],
                user_description=user_input,
                consultation=consultation,
            )

    # Sanitize "*" from LLM output
    clean_reply = sanitize_llm_output(explanation)

    # Add assistant reply
    add_message(consultation, "assistant", clean_reply)
    save_active_consultation(consultation)

    # CLEAR pending bytes and bump uploader revision
    st.session_state["pending_image_bytes"] = None
    st.session_state["uploader_rev"] += 1

    # Rerun to redraw chat with new messages and a fresh empty uploader
    st.rerun()
