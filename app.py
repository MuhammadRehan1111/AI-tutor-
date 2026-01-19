import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
from kb_manager import KBManager
from memory_manager import MemoryManager
from prompts import SYSTEM_PROMPT

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="Tutor - Your Smart AI Assistant", page_icon="🎓", layout="wide")

# Custom CSS for a friendly, motivated look
st.markdown("""
<style>
    .main {
        background-color: #f0f7f9;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 10px;
    }
    .stSidebar {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "kb" not in st.session_state:
    st.session_state.kb = KBManager()
if "memory" not in st.session_state:
    st.session_state.memory = MemoryManager()

# Sidebar - Student Profile & Knowledge Base
with st.sidebar:
    st.title("🎓 Tutor Profile")
    st.info(st.session_state.memory.get_context_summary())
    
    st.divider()
    
    st.subheader("📚 Knowledge Base")
    uploaded_files = st.file_uploader("Upload books, notes, or PDFs", accept_multiple_files=True)
    if st.button("Add to Knowledge Base"):
        if uploaded_files:
            with st.spinner("Tutor is processing your materials..."):
                sources = st.session_state.kb.process_files(uploaded_files)
                st.success(f"Stored! I've added {sources} to our study collection. 🚀")
        else:
            st.warning("Please select files first!")

    st.divider()
    st.subheader("🎯 Weak Topics")
    for topic in st.session_state.memory.memory["weak_topics"]:
        st.write(f"- {topic}")

# Main Chat Interface
st.title("Hi! I'm Tutor. Let's learn together! 🌟")

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("Please set your GOOGLE_API_KEY in a .env file.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("What are we studying today?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Tutor is thinking..."):
            # 1. Search KB
            kb_context = st.session_state.kb.query_kb(prompt)
            
            # 2. Get Memory Context
            student_context = st.session_state.memory.get_context_summary()
            
            # 3. Construct Final Prompt
            full_prompt = f"""
{SYSTEM_PROMPT}

### STUDENT CONTEXT
{student_context}

### KNOWLEDGE BASE EXCERPT (PRIORITY)
{kb_context if kb_context else "No specific documents found. Use general knowledge if needed but remind student to upload materials if they have them."}

### QUESTION
{prompt}
"""
            
            try:
                response = model.generate_content(full_prompt)
                tutor_reply = response.text
                st.markdown(tutor_reply)
                
                # Update History & Memory
                st.session_state.messages.append({"role": "assistant", "content": tutor_reply})
                st.session_state.memory.add_to_history(prompt, tutor_reply)
                
                # Basic sentiment/intent check for weak topics (Simple heuristic)
                if "struggling with" in prompt.lower() or "don't understand" in prompt.lower():
                    # Extract a likely topic - very simple for MVP
                    topic = prompt.lower().split("about")[-1].strip()
                    st.session_state.memory.add_weak_topic(topic)
                    
            except Exception as e:
                st.error(f"Oops! Something went wrong: {e}")

    # Check for name update (Self-intro)
    if "my name is" in prompt.lower():
        name = prompt.lower().split("is")[-1].strip().capitalize()
        st.session_state.memory.update_profile(name=name)
        st.rerun()
