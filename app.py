# app.py : Basic Q&A Chatbot (LangChain + Groq + Streamlit)
# Chalane ka tareeqa (terminal me):  streamlit run app.py

import os
import streamlit as st
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser

# ---------------------------------------------------------------
# 1. Page setup
# ---------------------------------------------------------------
st.set_page_config(page_title="Q&A Chatbot", page_icon="💬")
st.title("💬 Q&A Chatbot")

# ---------------------------------------------------------------
# 2. API key
# Local par .env se aati hai, deploy par Streamlit "Secrets" se.
# Key code me kabhi nahi likhte.
# ---------------------------------------------------------------
load_dotenv()

def get_api_key():
    try:
        return st.secrets["GROQ_API_KEY"]      # deployed app
    except Exception:
        return os.getenv("GROQ_API_KEY")       # local (.env)

api_key = get_api_key()
if not api_key:
    st.error("GROQ_API_KEY nahi mili. .env (local) ya Streamlit Secrets (deploy) me daalo.")
    st.stop()

# ---------------------------------------------------------------
# 3. Sidebar: model chunna aur chat clear karna
# ---------------------------------------------------------------
with st.sidebar:
    st.header("Settings")
    model_name = st.selectbox("Model", ["openai/gpt-oss-20b", "openai/gpt-oss-120b"])
    if st.button("Chat clear karo"):
        st.session_state.messages = []

# ---------------------------------------------------------------
# 4. Chain (notebook wali hi: prompt -> model -> parser)
# cache_resource: har rerun par dobara na banay, ek baar bane aur yaad rahe
# ---------------------------------------------------------------
@st.cache_resource
def build_chain(model_name, api_key):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Tum ek helpful assistant ho. Jawab Roman Urdu me do, simple language me."),
        MessagesPlaceholder("history"),
        ("human", "{question}"),
    ])
    llm = ChatGroq(model=model_name, api_key=api_key)
    return prompt | llm | StrOutputParser()

chain = build_chain(model_name, api_key)

# ---------------------------------------------------------------
# 5. Memory
# Streamlit har click/message par poori script dobara chalata hai,
# isliye normal variable (history = []) har baar khali ho jata.
# st.session_state wo jagah hai jo reruns ke beech bachi rehti hai.
# ---------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []     # [{"role": "user"/"assistant", "content": "..."}]

# Purani chat screen par dobara dikhao
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------------------------------------------------------------
# 6. Naya sawal
# ---------------------------------------------------------------
question = st.chat_input("Apna sawal likho...")

if question:
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            # stream: jawab lafz ba lafz screen par aata hai
            # history me abhi naya sawal shamil nahi (wo niche append hoga)
            answer = st.write_stream(
                chain.stream({"question": question, "history": st.session_state.messages})
            )
            # Jawab kamyabi se aaya to hi history me save karo
            st.session_state.messages.append({"role": "user", "content": question})
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"Error aaya: {e}")