# consultations.py

import streamlit as st
from datetime import datetime
from utils import now_str


# ------------------------------------------------------------
# CREATE NEW CONSULTATION
# ------------------------------------------------------------

def create_new_consultation():
    """
    Create a new consultation with:
    - empty chat history
    - onboarding state reset
    - patient info empty
    """

    new_consultation = {
        "id": len(st.session_state.consultations) + 1,
        "title": f"Consultation {len(st.session_state.consultations) + 1}",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),

        # Patient onboarding info stored per consultation
        "patient_name": None,
        "patient_age": None,
        "skin_type": None,
        "problem_type": None,

        "onboarding_step": 1,   # 1 = ask name first
        "messages": [],         # list of {role, content, timestamp}
    }

    st.session_state.consultations.append(new_consultation)
    st.session_state.active_consultation = len(st.session_state.consultations) - 1


# ------------------------------------------------------------
# SWITCH CONSULTATION
# ------------------------------------------------------------

def switch_consultation(index: int):
    """Switch the active consultation."""
    if 0 <= index < len(st.session_state.consultations):
        st.session_state.active_consultation = index


# ------------------------------------------------------------
# RENAME CONSULTATION
# ------------------------------------------------------------

def rename_consultation(index: int, new_title: str):
    """Rename the title of a consultation."""
    if 0 <= index < len(st.session_state.consultations):
        st.session_state.consultations[index]["title"] = new_title


# ------------------------------------------------------------
# SIDEBAR CONSULTATION LIST
# ------------------------------------------------------------

def render_consultation_sidebar():
    """Render the sidebar with consultations list and actions."""

    st.markdown(
        "<div class='sidebar-title'>💬 Consultations</div>",
        unsafe_allow_html=True,
    )

    if not st.session_state.consultations:
        st.info("No consultations yet.")
        if st.button("➕ Start New Consultation"):
            create_new_consultation()
            st.rerun()
        return

    # Render list of consultations
    for i, c in enumerate(st.session_state.consultations):

        is_active = (i == st.session_state.active_consultation)
        css_class = "consult-item-active" if is_active else "consult-item"

        created = c["created_at"].strftime("%b %d, %H:%M")
        num_msgs = len(c["messages"])

        # Sidebar block
        st.markdown(
            f"""
            <div class="{css_class}">
                <div class="consult-title">{c["title"]}</div>
                <div class="consult-meta">
                    Started: {created} • Messages: {num_msgs}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Open / Rename controls
        col1, col2 = st.columns([0.6, 0.4])
        with col1:
            if st.button(f"Open #{c['id']}", key=f"open_{c['id']}"):
                switch_consultation(i)
                st.rerun()

        with col2:
            new_title = st.text_input(
                f"Rename_{c['id']}",
                value=c["title"],
                label_visibility="collapsed",
                key=f"title_{c['id']}"
            )
            rename_consultation(i, new_title)

        st.markdown("---")

    # Button to create a new consultation
    
