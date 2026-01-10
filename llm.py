# # llm.py
#from dotenv import load_dotenv
#import os
# import json
# import logging
# from groq import Groq

# # ------------------------------------------------------------
# # LOGGER CONFIG
# # ------------------------------------------------------------
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

# if not logger.handlers:
#     handler = logging.StreamHandler()
#     formatter = logging.Formatter(
#         "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#     )
#     handler.setFormatter(formatter)
#     logger.addHandler(handler)

# # ------------------------------------------------------------
# # Groq API Key
# # ------------------------------------------------------------
# llm.py
# llm.py

from dotenv import load_dotenv
import os
import json
import logging
from groq import Groq

# ------------------------------------------------------------
# LOGGER CONFIG
# ------------------------------------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# ------------------------------------------------------------
# Groq API Key (load from environment, NOT hard-coded)
# ------------------------------------------------------------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable is not set.")

logger.info("Initializing Groq client...")
try:
    client = Groq(api_key=GROQ_API_KEY)
    logger.info("Groq client initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Groq client: {e}")


# ------------------------------------------------------------
# CHAT HISTORY HELPERS
# ------------------------------------------------------------

def _build_chat_history(consultation, max_messages: int = 12):
    """
    Take the last `max_messages` from the consultation messages
    and sanitize them for JSON (remove bytes, etc.).
    """
    raw = consultation.get("messages", []) or []
    history_raw = raw[-max_messages:]

    sanitized = []
    for m in history_raw:
        # Drop non-JSON-serializable fields like image_bytes
        msg = {k: v for k, v in m.items() if k != "image_bytes"}

        # If there was an image, add a simple boolean flag
        if "image_bytes" in m:
            msg["has_image"] = True

        sanitized.append(msg)

    return sanitized


def _build_context_summary(chat_history):
    """
    Lightweight heuristic summary of the last few user + assistant turns.
    No extra LLM call, just string stitching.
    """
    user_lines = [m.get("content", "") for m in chat_history if m.get("role") == "user"]
    ai_lines = [m.get("content", "") for m in chat_history if m.get("role") == "assistant"]

    last_user = user_lines[-2:]  # last 2 user turns
    last_ai = ai_lines[-1:]      # last AI turn

    parts = []
    if last_user:
        parts.append("Recent user messages: " + " | ".join(last_user))
    if last_ai:
        parts.append("Last assistant message: " + " | ".join(last_ai))

    return " ".join(parts) if parts else ""


# ------------------------------------------------------------
# FORMAT CLIP PREDICTIONS + CONTEXT FOR LLM
# ------------------------------------------------------------

def prepare_prediction_payload(predictions, user_description, consultation):
    """
    Format CLIP predictions + user info + description + chat history
    into a JSON payload the LLM can use.
    """

    chat_history = _build_chat_history(consultation)
    context_summary = _build_context_summary(chat_history)

    payload = {
        "predictions": predictions,                # list of CLIPSkinDetector results
        "priority": "Rank 1 = highest likelihood",
        "user_description": user_description,      # latest user text
        "current_question": user_description,      # what LLM must answer now
        "chat_history": chat_history,              # recent conversation slice (sanitized)
        "context_summary": context_summary,        # small recap
        "patient": {
            "name": consultation.get("patient_name"),
            "age": consultation.get("patient_age"),
            "skin_type": consultation.get("skin_type"),
            "problem_type": consultation.get("problem_type"),
        },
    }

    # Log a safe preview of payload
    try:
        preview = json.dumps(payload, indent=2)
        preview = preview[:800] + " ... (truncated)" if len(preview) > 800 else preview
        logger.info(f"[Groq Input Payload] {preview}")
    except Exception as e:
        logger.warning(f"Failed to log payload preview: {e}")

    return payload


# ------------------------------------------------------------
# MAIN FUNCTION: EXPLAIN RESULTS WITH GROQ
# ------------------------------------------------------------

def explain_with_groq(predictions, user_description, consultation):
    """
    Sends CLIP predictions + user description + patient info + chat history
    to Groq and returns a short DermaCare-style explanation.
    """

    payload = prepare_prediction_payload(predictions, user_description, consultation)

    system_prompt = """
You are **DermaCare AI**, a friendly virtual dermatologist assistant.

You always receive a JSON payload with:
- predictions: list of objects from the image model, each with:
  - rank (1 = most likely)
  - confidence (0–100)
  - disease, severity, characteristics, recommendation
- user_description: the patient's latest text in their own words
- current_question: the specific question you must answer now
- chat_history: recent conversation with role + content + timestamp
- context_summary: short recap of recent discussion
- patient: { name, age, skin_type, problem_type }

YOUR APPROACH:

1. **Use Context**: Review chat_history and context_summary to understand what has been discussed. Don't repeat previous explanations.

2. **Answer Only What's Asked**: 
   - If user asks for DETECTION/IDENTIFICATION → Provide condition name, characteristics, and severity. DO NOT give treatment unless asked.
   - If user asks for TREATMENT/REMEDIES/CURE → Provide specific care steps, products, and recommendations. DO NOT repeat detection details.
   - If user asks a FOLLOW-UP question → Answer that specific question based on chat history.

3. **When Predictions are Present** (user uploaded an image):
   - Use the "disease" field from top prediction
   - NEVER mention confidence percentages
   - For detection queries: Name the condition + brief description + characteristics
   - For treatment queries: Give practical care steps and recommendations

4. **When No Predictions** (no image):
   - Use chat_history and user_description to provide relevant guidance
   - Answer based on conversation context

5. **Treatment Guidelines** (only when user asks):
   - Home care measures
   - Over-the-counter products (specific names when helpful)
   - When to see a dermatologist
   - Lifestyle and prevention tips

6. **Strict Boundaries**:
   - ONLY answer skin, dermatology, and skincare questions
   - If current_question is NOT skin-related, reply: "Sorry, I can only help with skin-related questions."
   - Do NOT provide medical diagnoses - this is appearance-based analysis only

STYLE:
- Be concise and precise - avoid lengthy explanations
- Natural, conversational tone
- Professional but friendly
- Match response length to question complexity
- End with: "How can I help you next?" or contextual closing like "Take care!" or "Feel free to ask more!"

IMPORTANT RULES:
- Never show confidence percentages
- Never repeat information already discussed in chat_history
- Detection requests = name + description only
- Treatment requests = remedies + care steps only
- Non-skin questions = politely decline
"""

    user_prompt = (
        "Here is the structured analysis input:\n\n"
        + json.dumps(payload, indent=2)
        + "\n\nPlease generate the answer following the instructions."
    )

    logger.info(
        f"[Groq Request] system_prompt_length={len(system_prompt)}, "
        f"user_prompt_length={len(user_prompt)}"
    )

    try:
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=500,  # keep answers short
        )

        raw_text = response.choices[0].message.content
        preview = raw_text[:800] + " ... (truncated)" if len(raw_text) > 800 else raw_text
        logger.info(f"[Groq Response Preview] {preview}")

        return raw_text

    except Exception as e:
        logger.error("Groq LLM Error", exc_info=True)
        return (
            "⚠️ Sorry, I couldn't generate a response right now.\n"
            f"Error: {str(e)}"
        )
