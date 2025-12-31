import streamlit as st
import os
from dotenv import load_dotenv
from ai_engine import CareerAIEngine
from utils import convert_pdf_to_image, extract_text_from_pdf

# --- PAGE CONFIG ---
st.set_page_config(page_title="RAG-Based Freelancer Assistant", layout="wide", page_icon="🚀")
load_dotenv()
st.title("🤖 RAG-Based Freelancer Assistant")

# --- VALIDATION ---
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ GOOGLE_API_KEY not found in .env")
    st.stop()

if 'engine' not in st.session_state:
    with st.spinner("Initializing Native AI Engine..."):
        st.session_state['engine'] = CareerAIEngine(api_key)
        st.success(f"Connected: {st.session_state['engine'].model_name}")

with st.sidebar:
    st.header("Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        
        if 'last_uploaded' not in st.session_state or st.session_state['last_uploaded'] != uploaded_file.name:
            with st.spinner("Processing..."):
                st.session_state['resume_image'] = convert_pdf_to_image(file_bytes)
                st.session_state['resume_text'] = extract_text_from_pdf(file_bytes)
                st.session_state['last_uploaded'] = uploaded_file.name
                
                st.session_state['chat_session'] = st.session_state['engine'].start_chat_session(
                    st.session_state['resume_text']
                )
            st.success("Loaded!")
        
    if st.button("Reset App"):
        st.session_state.clear()
        st.rerun()

if 'resume_image' in st.session_state:
    
    st.markdown("### 📝 Visual Critique")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.image(st.session_state['resume_image'], caption="Original Resume", use_container_width=True)
    
    with col2:
        st.write("**AI Red Pen Analysis**")
        
        if st.button("🔍 Analyze Resume", type="primary"):
            with st.spinner("AI is grading your resume..."):
                engine = st.session_state['engine']
                result = engine.analyze_resume_vision(st.session_state['resume_image'])
                
                if isinstance(result, dict) and "error" in result:
                    st.error(f"❌ Analysis Failed: {result['error']}")
                    st.info("Tip: If it says 'Quota', just wait 60 seconds and try again.")
                elif result:
                    annotated = engine.draw_red_pen(st.session_state['resume_image'], result)
                    st.session_state['annotated_image'] = annotated
                else:
                    st.error("Unknown Error. Please reset the app.")
        
        if 'annotated_image' in st.session_state:
            st.image(st.session_state['annotated_image'], caption="AI Critiques", use_container_width=True)

    st.divider() 

    st.markdown("### 💬 Career Assistant")
    
    if "ui_messages" not in st.session_state:
        st.session_state.ui_messages = [{"role": "assistant", "content": "Hello! Ask me about your resume, salary estimates, or missing skills."}]
    
    chat_container = st.container(height=500) 
    
    with chat_container:
        for msg in st.session_state.ui_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    if prompt := st.chat_input("Ex: 'What skills am I missing?'"):
        st.session_state.ui_messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response_text = st.session_state['engine'].run_chat(
                        st.session_state['chat_session'], 
                        prompt
                    )
                    st.markdown(response_text)
                    st.session_state.ui_messages.append({"role": "assistant", "content": response_text})

else:
    st.info("👋 Upload a PDF to start.")