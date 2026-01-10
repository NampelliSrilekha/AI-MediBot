# styles.py

def load_css():
    return """
    <style>

    /* App background */
    .stApp {
        background-color: #020617;
    }
    .main {
        background: radial-gradient(circle at top left, #1f2937 0, #020617 55%);
        color: #e5e7eb;
    }

    /* Chat bubbles */
    .chat-message {
        padding: 0.85rem 1.1rem;
        border-radius: 0.75rem;
        margin-bottom: 0.6rem;
        display: flex;
        flex-direction: column;
        font-size: 0.95rem;
        max-width: 80%;
    }
    .chat-message.user {
        margin-left: auto;
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: #f9fafb;
        box-shadow: 0 8px 16px rgba(79, 70, 229, 0.35);
    }
    .chat-message.assistant {
        margin-right: auto;
        background: #020617;
        border: 1px solid rgba(148, 163, 184, 0.4);
        color: #e5e7eb;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.8);
    }
    .chat-timestamp {
        font-size: 0.75rem;
        opacity: 0.7;
        margin-top: 0.25rem;
    }

    /* Sidebar */
    .sidebar-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #c7d2fe;
        margin-bottom: 0.4rem;
    }
    .consult-item {
        padding: 0.45rem 0.6rem;
        margin-bottom: 0.35rem;
        border-radius: 0.5rem;
        background-color: #020617;
        border: 1px solid #1f2937;
        cursor: pointer;
    }
    .consult-item-active {
        border: 1px solid #818cf8;
        background: linear-gradient(135deg, #020617, #111827);
    }
    .consult-title {
        font-size: 0.88rem;
        color: #e5e7eb;
    }
    .consult-meta {
        font-size: 0.75rem;
        color: #9ca3af;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 999px;
        padding: 0.35rem 0.9rem;
        border: none;
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #818cf8, #6366f1);
    }

    /* Chat input */
    .stChatInput input {
        background-color: #020617 !important;
        color: #e5e7eb !important;
        border-radius: 999px !important;
        border: 1px solid #4b5563 !important;
    }

    </style>
    """
