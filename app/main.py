"""
Ansira — Streamlit entrypoint.
Run from project root: streamlit run app/main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so `import app` works when running `streamlit run app/main.py`
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app import books as books_mod
from app import logger as log_mod
from app import orders as orders_mod
from app.chatbot import process_message

# --- Page config ---
st.set_page_config(
    page_title="Ansira — Book Shop",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CUSTOM_CSS = """
<style>
    /* Light shaded app background */
    [data-testid="stAppViewContainer"] {
        background-color: #f3f6fb;
    }
    [data-testid="stHeader"] {
        background: rgba(243, 246, 251, 0.85);
    }
    /* Main chat area */
    .stChatMessage {
        border-radius: 12px;
        background: #ffffff;
        border: 1px solid #e6ecf5;
        padding: 0.35rem 0.45rem;
    }
    div[data-testid="stVerticalBlock"] > div { gap: 0.5rem; }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #eef3fa;
    }
    section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
    .metric-row { font-size: 0.9rem; color: var(--secondary-text-color); }
</style>
"""
st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)


def init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I'm **Ansira** for Ansira Book Shop. "
                    "Ask about our FAQs, browse books, place an order (*e.g. I want to buy 2 copies of Atomic Habits*), "
                    "or check/cancel an order with your order number."
                ),
            }
        ]
    if "customer_name" not in st.session_state:
        st.session_state.customer_name = ""


def history_for_bot() -> list[dict[str, str]]:
    return [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]


def render_sidebar() -> None:
    with st.sidebar:
        st.title("📚 Ansira")
        st.caption("NLP customer assistant — local Mistral via Ollama")

        st.session_state.customer_name = st.text_input(
            "Your name (for orders)",
            value=st.session_state.customer_name,
            placeholder="Guest",
            help="Used as customer name when you place an order.",
        )

        st.divider()
        st.subheader("Session chat")
        # Compact history preview
        for i, m in enumerate(st.session_state.messages[-12:]):
            role = m["role"]
            preview = m["content"][:80] + ("…" if len(m["content"]) > 80 else "")
            st.caption(f"**{'You' if role=='user' else 'Bot'}:** {preview}")

        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Chat cleared. How can I help you today?",
                }
            ]
            st.rerun()

        st.divider()
        st.subheader("Try commands")
        st.caption("- Show me book list")
        st.caption("- Books in fiction category")
        st.caption("- Books by James Clear")
        st.caption("- I want to buy 2 copies of Atomic Habits")
        st.caption("- Check my order 10002")
        st.caption("- Cancel my order 10002")

        st.divider()
        st.subheader("Analytics")
        stats = log_mod.get_analytics_summary()
        st.metric("Total queries (logged)", stats.get("total_queries", 0))
        st.metric("Book searches", stats.get("book_searches", 0))
        st.metric("Orders placed", stats.get("orders_placed", 0))

        with st.expander("Admin: view JSON data", expanded=False):
            st.write("**Books (sample)**")
            st.json(books_mod.get_books()[:5])
            st.write("**Recent orders**")
            od = orders_mod.load_orders_data().get("orders", [])
            st.json(od[-5:] if od else [])


def main() -> None:
    init_session()

    render_sidebar()

    st.title("Ansira Book Shop")
    st.caption("FAQs · Browse · Order · Status · Cancel — powered by Ollama (Mistral)")
    st.info(
        "Try commands: **Show me book list**, **I want to buy 2 copies of Atomic Habits**, "
        "**Check my order 10002**, **Cancel my order 10002**"
    )

    # Display messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input: append user, generate reply, log, rerun so the chat loop renders consistently
    if prompt := st.chat_input("Ask anything about our shop or books…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Thinking…"):
            reply = process_message(
                prompt,
                conversation_history=history_for_bot()[:-1],
                session_customer_name=st.session_state.customer_name or None,
            )
            text = reply.text
        st.session_state.messages.append({"role": "assistant", "content": text})
        log_mod.log_interaction(prompt, text)
        st.rerun()


if __name__ == "__main__":
    main()
