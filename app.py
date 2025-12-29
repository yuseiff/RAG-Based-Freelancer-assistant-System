import streamlit as st
import os
from dotenv import load_dotenv
from ai_engine import CareerAIEngine
from utils import convert_pdf_to_image, extract_text_from_pdf

st.set_page_config(page_title="AI Career Platform", layout="wide", page_icon="🚀")
load_dotenv()
st.title("🎓 Smart Freelance Platform")

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("❌ GOOGLE_API_KEY not found in .env")
    st.stop()

if 'engine' not in st.session_state:
    with st.spinner("Connecting to AI..."):
        st.session_state['engine'] = CareerAIEngine(api_key)
        st.success(f"Connected: {st.session_state['engine'].working_model_name}")

with st.sidebar:
    st.header("Upload Resume")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        if 'resume_image' not in st.session_state:
            with st.spinner("Processing..."):
                st.session_state['resume_image'] = convert_pdf_to_image(file_bytes)
                st.session_state['resume_text'] = extract_text_from_pdf(file_bytes)
        st.success("Loaded!")
    if st.button("Reset"):
        st.session_state.clear()
        st.rerun()

if 'resume_image' in st.session_state:
    tab1, tab2 = st.tabs(["📝 Visual Critique", "💬 Chat Assistant"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1: st.image(st.session_state['resume_image'], caption="Original", use_container_width=True)
        with col2:
            if st.button("🔍 Analyze Resume", type="primary"):
                with st.spinner("Analyzing..."):
                    engine = st.session_state['engine']
                    coords = engine.analyze_resume_vision(st.session_state['resume_image'])
                    if coords:
                        annotated = engine.draw_red_pen(st.session_state['resume_image'], coords)
                        st.session_state['annotated_image'] = annotated
                    else: st.error("No critiques found.")
            if 'annotated_image' in st.session_state:
                st.image(st.session_state['annotated_image'], caption="AI Critiques", use_container_width=True)

    with tab2:
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Hello! Ask me anything about your resume."}]
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        if prompt := st.chat_input("Ex: 'How can I improve my Summary?'"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    engine = st.session_state['engine']
                    response = engine.run_chat_agent(prompt, st.session_state['resume_text'])
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
else:
    st.info("👋 Upload a PDF to start.")