import os
import uuid

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="ShopEasy Support", page_icon="🛒", layout="centered")

st.title("ShopEasy Customer Support")
st.caption("Powered by LangGraph + AWS Bedrock")

# Keep session state across reruns
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_intent" not in st.session_state:
    st.session_state.last_intent = ""

# Sidebar shows the session ID and last detected intent
with st.sidebar:
    st.subheader("Session Info")
    st.code(st.session_state.session_id, language=None)
    st.caption("This ID keeps your conversation alive. Pass it in Postman too.")

    if st.session_state.last_intent:
        st.subheader("Last Detected Intent")
        st.info(st.session_state.last_intent)

    if st.button("Reset Conversation"):
        requests.post(
            f"{BACKEND_URL}/chat/reset",
            params={"session_id": st.session_state.session_id},
        )
        st.session_state.messages = []
        st.session_state.last_intent = ""
        st.rerun()

    st.divider()
    st.subheader("Try These")
    st.markdown("""
1. Where is my order ORD-1001?
2. Can I return it?
3. Is the Webcam in stock?
4. I want to speak to a manager!
""")

# Chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={
                        "message": user_input,
                        "session_id": st.session_state.session_id,
                    },
                    timeout=60,
                )
                data = resp.json()
                reply = data.get("reply", "Something went wrong.")
                st.session_state.last_intent = data.get("intent", "")
            except requests.exceptions.ConnectionError:
                reply = "Cannot connect to backend. Make sure the FastAPI server is running on port 8000."

        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()
