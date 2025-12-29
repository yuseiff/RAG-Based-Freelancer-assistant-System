import streamlit as st
import os
import json
import base64
import re
from io import BytesIO
from pdf2image import convert_from_bytes
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import PyPDF2

# --- GOOGLE GEMINI IMPORTS ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Standard LangChain Imports
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
# create_react_agent is definitely in 'langchain.agents' in the latest version
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools.retriever import create_retriever_tool
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

# --- CONFIGURATION ---
st.set_page_config(page_title="AI Smart Platform", layout="wide", page_icon="🎓")
load_dotenv()

# VALIDATION: Check for Google Key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("🚨 CRITICAL: GOOGLE_API_KEY not found in .env file.")
    st.info("Get one here: https://aistudio.google.com/app/apikey")
    st.stop()

# ==========================================
# PART 1: VISION ENGINE (Powered by Gemini 1.5 Flash)
# ==========================================
class ResumeAnnotator:
    def __init__(self, api_key):
        # Gemini 1.5 Flash is fast, cheap/free, and great at vision
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.1
        )

    def analyze_and_get_coordinates(self, image):
        """
        Sends the PIL image directly to Gemini to get JSON coordinates.
        """
        prompt = """
        You are a Senior Technical Recruiter. Review this resume image.
        Identify 3 CRITICAL weak spots (e.g., generic bullet points, missing metrics, bad formatting, wasted whitespace).
        
        Return ONLY a JSON object with this schema (NO markdown, NO extra text):
        { "critiques": [ { "type": "circle", "x": 50, "y": 20, "comment": "Quantify this!" } ] }
        
        Constraint: 'x' and 'y' are percentages (0-100) representing location on the page.
        x=0 is left, x=100 is right. y=0 is top, y=100 is bottom.
        """
        
        # Gemini handles PIL images natively in the message content
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": image} # LangChain adapter handles PIL conversion automatically
            ]
        )

        try:
            response = self.llm.invoke([message])
            content = response.content
            
            # Clean up the response (Gemini sometimes adds ```json ... ```)
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
            
        except Exception as e:
            st.error(f"Gemini Vision Error: {e}")
            return None

    def draw_annotations(self, image, annotations):
        """
        Draws the red pen overlay using the coordinates from Gemini.
        """
        if not annotations or "critiques" not in annotations: return image
        overlay = image.copy()
        draw = ImageDraw.Draw(overlay)
        width, height = overlay.size
        
        try: font = ImageFont.truetype("arial.ttf", int(height * 0.02))
        except: font = ImageFont.load_default()

        for item in annotations["critiques"]:
            # Coordinate Math
            cx, cy = (item['x'] / 100) * width, (item['y'] / 100) * height
            r_x, r_y = width * 0.15, height * 0.05
            
            # Draw Circle
            draw.ellipse([cx - r_x/2, cy - r_y/2, cx + r_x/2, cy + r_y/2], outline="red", width=5)
            
            # Draw Text Label
            text = f"⚠️ {item['comment']}"
            bbox = draw.textbbox((cx, cy), text, font=font)
            text_w, text_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            
            # Smart Text Positioning
            tx, ty = cx + r_x/2 + 10, cy - text_h/2
            if tx + text_w > width: tx = cx - r_x/2 - text_w - 10
            if tx < 0: tx = 10 # Prevent going off left edge
            
            draw.rectangle([tx-5, ty-5, tx+text_w+5, ty+text_h+5], fill="white", outline="red", width=2)
            draw.text((tx, ty), text, fill="red", font=font)
            
        return overlay

# ==========================================
# PART 2: TEXT AGENT TOOLS
# ==========================================

def extract_text_from_pdf(file_bytes):
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except: return ""

@st.cache_resource
def setup_knowledge_base():
    # Mock Knowledge Base
    kb_text = """
    # SALARY NEGOTIATION
    - Always ask for a budget range first.
    # INTERVIEW TIPS
    - Use the STAR Method (Situation, Task, Action, Result).
    """
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = [Document(page_content=x) for x in splitter.split_text(kb_text)]
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = FAISS.from_documents(docs, embeddings)
    return vector_store.as_retriever()

retriever_tool = create_retriever_tool(setup_knowledge_base(), "career_guide", "Search for interview/salary advice.")

@tool
def job_search_tool(query: str):
    """Searches for job listings. Input: 'Python Developer'."""
    return f"Found 3 listings for {query}: 1. Senior Role ($120k), 2. Junior Role ($80k)."

@tool
def salary_estimator(query: str):
    """
    Estimates market salary. 
    Input: A string describing the role and years of experience.
    Example: "Data Scientist, 5 years" or just "Java Developer"
    """
    if "," in query:
        role = query.split(",")[0]
        years_str = query.split(",")[1]
    else:
        role = query
        years_str = "3" # Default
        
    try:
        years = int(re.search(r'\d+', years_str).group())
    except:
        years = 3
        
    est = 50000 + (years * 12000)
    return f"Estimated Salary for {role} ({years} yrs): ${est:,}"

tools = [retriever_tool, job_search_tool, salary_estimator]

# ==========================================
# PART 3: GEMINI AGENT INITIALIZATION
# ==========================================
# We use Gemini 1.5 Flash for the chat agent too
llm_chat = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=api_key,
    temperature=0.3
)

prompt_template = PromptTemplate.from_template("""
You are a Career Assistant. 
USER RESUME CONTEXT: {resume_context}

TOOLS AVAILABLE:
{tools}

Use the following format:
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action

If you have the answer or don't need a tool:
Thought: Do I need to use a tool? No
Final Answer: [your response]

User Question: {input}
Thought:{agent_scratchpad}
""")

agent = create_react_agent(llm_chat, tools, prompt_template)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

# ==========================================
# PART 4: MAIN UI
# ==========================================
annotator = ResumeAnnotator(api_key)

st.title("🎓 Smart Freelance Platform: Gemini Edition")

with st.sidebar:
    st.header("Step 1: Upload")
    uploaded_file = st.file_uploader("Upload PDF Resume", type=["pdf"])
    
    if uploaded_file:
        file_bytes = uploaded_file.getvalue()
        
        # Process Image (Vision)
        if 'resume_image' not in st.session_state:
            with st.spinner("Processing PDF to Image..."):
                images = convert_from_bytes(file_bytes, dpi=200) # 200 DPI is good for OCR
                if images: st.session_state['resume_image'] = images[0]
        
        # Process Text (Chat)
        if 'resume_text' not in st.session_state:
            text = extract_text_from_pdf(file_bytes)
            st.session_state['resume_text'] = text
            
        st.success("Resume Loaded!")
        
    if st.button("Reset App"):
        st.session_state.clear()
        st.rerun()

if 'resume_image' in st.session_state:
    
    tab1, tab2 = st.tabs(["📝 Visual Critique", "💬 Chat Assistant"])
    
    # TAB 1: VISUAL
    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(st.session_state['resume_image'], caption="Original", use_container_width=True)
        with col2:
            st.write("### Gemini Visual Analysis")
            if st.button("🔍 Run Red Pen Critique", type="primary"):
                with st.spinner("Gemini is reading your resume..."):
                    coords = annotator.analyze_and_get_coordinates(st.session_state['resume_image'])
                    if coords:
                        annotated = annotator.draw_annotations(st.session_state['resume_image'], coords)
                        st.session_state['annotated_image'] = annotated
            
            if 'annotated_image' in st.session_state:
                st.image(st.session_state['annotated_image'], caption="AI Critiques", use_container_width=True)

    # TAB 2: CHAT
    with tab2:
        st.subheader("Chat with your Resume")
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "I've analyzed your resume text. Ask me about salaries, improvements, or job matches!"}]

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ex: 'What skills am I missing?'"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = agent_executor.invoke({
                            "input": prompt,
                            "resume_context": st.session_state['resume_text']
                        })
                        output = response["output"]
                        st.markdown(output)
                        st.session_state.messages.append({"role": "assistant", "content": output})
                    except Exception as e:
                        st.error(f"Agent Error: {e}")

else:
    st.info("👋 Upload a PDF to start.")