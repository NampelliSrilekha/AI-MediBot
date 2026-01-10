# onboarding.py

import streamlit as st
from utils import add_message, save_active_consultation
from typing import Optional

def handle_onboarding(consultation, user_input: Optional[str] = None) -> bool:

    """
    Onboarding steps PER consultation:

    1. (step 1) Send greeting + ask for name (no user_input expected)
    2. (step 2) Read name from user_input -> ask age
    3. (step 3) Read age -> show skin type buttons
    4. (step 4) Read skin type (from buttons) -> show problem type buttons
    5. (step 5) Read problem type (from buttons) -> summary -> onboarding complete

    Returns:
        True  -> onboarding still in progress
        False -> onboarding finished (step = 999)
    """

    step = consultation.get("onboarding_step", 1)

    # -------------------------
    # STEP 1: Send initial greeting ONCE
    # -------------------------
    if step == 1:
        # We don't expect any user_input here – just send greeting
        add_message(
            consultation,
            "assistant",
            "Welcome! Before we begin, may I know your full name?",
        )
        consultation["onboarding_step"] = 2
        save_active_consultation(consultation)
        return True

    # -------------------------
    # STEP 2: Get NAME
    # -------------------------
    if step == 2:
        if not user_input or len(user_input.strip()) < 2:
            add_message(
                consultation,
                "assistant",
                "Please enter a valid full name.",
            )
            save_active_consultation(consultation)
            return True

        consultation["patient_name"] = user_input.strip()
        consultation["onboarding_step"] = 3
        save_active_consultation(consultation)

        add_message(
            consultation,
            "assistant",
            f"Nice to meet you, {consultation['patient_name']}! 😊\n\n"
            "How old are you?",
        )
        save_active_consultation(consultation)
        return True

    # -------------------------
    # STEP 3: Get AGE
    # -------------------------
    if step == 3:
        if not user_input or not user_input.isdigit():
            add_message(
                consultation,
                "assistant",
                "Please enter a valid age (e.g., 25).",
            )
            save_active_consultation(consultation)
            return True

        age_val = int(user_input)
        if age_val <= 0 or age_val > 110:
            add_message(
                consultation,
                "assistant",
                "Please enter a realistic age (e.g., between 1 and 110).",
            )
            save_active_consultation(consultation)
            return True

        consultation["patient_age"] = str(age_val)
        consultation["onboarding_step"] = 4
        save_active_consultation(consultation)

        add_message(
            consultation,
            "assistant",
            "Great! What is your skin type?",
        )
        save_active_consultation(consultation)
        return True

    # -------------------------
    # STEP 4: Get SKIN TYPE (buttons)
    # -------------------------
    if step == 4:
        if not user_input or user_input.lower() not in {"normal", "oily", "dry"}:
            # If invalid or empty, ask again – buttons will be shown from app.py
            add_message(
                consultation,
                "assistant",
                "Please choose your skin type using the buttons: Normal / Oily / Dry.",
            )
            save_active_consultation(consultation)
            return True

        consultation["skin_type"] = user_input.capitalize()
        consultation["onboarding_step"] = 5
        save_active_consultation(consultation)

        add_message(
            consultation,
            "assistant",
            "Got it! What kind of skin issue are you facing?",
        )
        save_active_consultation(consultation)
        return True

    # -------------------------
    # STEP 5: Get PROBLEM TYPE (buttons)
    # -------------------------
    if step == 5:
        valid_map = {
            "acne": "Acne / Pimples",
            "pimples": "Acne / Pimples",
            "rash": "Rashes / Redness",
            "rashes": "Rashes / Redness",
            "pigmentation": "Pigmentation",
            "pigment": "Pigmentation",
            "infection": "Infection / Fungal",
            "fungal": "Infection / Fungal",
            "wound": "Wound / Cut",
            "other": "Other",
        }

        if not user_input or user_input.lower() not in valid_map:
            add_message(
                consultation,
                "assistant",
                "Please choose your problem type using the buttons.",
            )
            save_active_consultation(consultation)
            return True

        consultation["problem_type"] = valid_map[user_input.lower()]
        consultation["onboarding_step"] = 999  # done
        save_active_consultation(consultation)

        add_message(
            consultation,
            "assistant",
            f"Thank you! 😊 You're all set.\n\n"
            f"Summary:\n"
            f"- Name: {consultation['patient_name']}\n"
            f"- Age: {consultation['patient_age']}\n"
            f"- Skin Type: {consultation['skin_type']}\n"
            f"- Problem Type: {consultation['problem_type']}\n\n"
            "Now you can describe your issue in more detail or upload a clear picture "
            "of the affected area so I can guide you better.",
        )
        save_active_consultation(consultation)
        return False

    # already completed
    return False


# ------------------------------------------------------------
# BUTTON HELPERS (RETURN STRING, NOT SESSION FLAGS)
# ------------------------------------------------------------

def render_skin_type_buttons():
    """Return selected skin type string if a skin-type button is clicked."""
    col1, col2, col3 = st.columns(3)
    choice = None
    with col1:
        if st.button("Normal"):
            choice = "normal"
    with col2:
        if st.button("Oily"):
            choice = "oily"
    with col3:
        if st.button("Dry"):
            choice = "dry"
    return choice


def render_problem_type_buttons():
    """Return selected problem type string if a problem-type button is clicked."""
    col1, col2, col3 = st.columns(3)
    choice = None
    with col1:
        if st.button("Acne / Pimples"):
            choice = "acne"
        if st.button("Pigmentation"):
            choice = "pigmentation"
    with col2:
        if st.button("Rashes / Redness"):
            choice = "rash"
        if st.button("Infection / Fungal"):
            choice = "infection"
    with col3:
        if st.button("Wound / Cut"):
            choice = "wound"
        if st.button("Other"):
            choice = "other"
    return choice
