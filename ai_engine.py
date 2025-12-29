# ai_engine.py
import json
import random
from PIL import ImageDraw, ImageFont

# Native SDK for Vision
import google.generativeai as genai

# LangChain & LangGraph for Chat
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent # <--- THE FIX YOU REQUESTED

from utils import image_to_base64

class CareerAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # --- AUTO-DISCOVERY ---
        self.working_model_name = self._find_working_model()
        print(f"✅ System locked onto model: {self.working_model_name}")

    def _find_working_model(self):
        """Finds a working model ID available to your API key."""
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            preferences = [
                "models/gemini-1.5-flash",
                "models/gemini-1.5-flash-latest",
                "models/gemini-1.5-flash-001",
                "models/gemini-pro"
            ]
            for pref in preferences:
                if pref in available_models: return pref
            for model in available_models:
                if "flash" in model: return model
            if available_models: return available_models[0]
            return "models/gemini-1.5-flash"
        except:
            return "models/gemini-1.5-flash"

    # --- VISION ENGINE (Native SDK) ---
    def analyze_resume_vision(self, image):
        prompt = """
        You are a Senior Technical Recruiter using a Red Pen. 
        Identify 3-4 CRITICAL weak spots in this resume.
        Return ONLY a JSON object with this exact schema (no markdown):
        { "critiques": [ { "type": "circle", "x": 50, "y": 20, "comment": "Quantify this!" } ] }
        Constraint: 'x' and 'y' are percentages (0-100).
        """
        try:
            model = genai.GenerativeModel(self.working_model_name)
            response = model.generate_content([prompt, image])
            content = response.text.replace("```json", "").replace("```", "").strip()
            if "{" in content:
                content = content[content.find("{"):content.rfind("}")+1]
            return json.loads(content)
        except Exception as e:
            print(f"Vision Failed: {e}")
            return None

    def draw_red_pen(self, image, annotations):
        if not annotations or "critiques" not in annotations: return image
        overlay = image.copy()
        draw = ImageDraw.Draw(overlay)
        width, height = overlay.size
        try: font = ImageFont.truetype("arial.ttf", int(height * 0.02))
        except: font = ImageFont.load_default()

        for item in annotations["critiques"]:
            cx, cy = (item['x'] / 100) * width, (item['y'] / 100) * height
            r_x, r_y = width * 0.15, height * 0.05
            for _ in range(3):
                ox, oy = random.randint(-2, 2), random.randint(-2, 2)
                draw.ellipse([cx-r_x/2+ox, cy-r_y/2+oy, cx+r_x/2+ox, cy+r_y/2+oy], outline="red", width=3)
            text = f"❌ {item['comment']}"
            bbox = draw.textbbox((cx, cy), text, font=font)
            text_w, text_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
            tx, ty = cx + r_x/2 + 10, cy - text_h/2
            if tx + text_w > width: tx = width - text_w - 10
            draw.rectangle([tx-5, ty-5, tx+text_w+5, ty+text_h+5], fill="#ffffcc", outline="red", width=2)
            draw.text((tx, ty), text, fill="red", font=font)
        return overlay

    # --- CHAT ENGINE (Updated to LangGraph) ---
    def run_chat_agent(self, user_query, resume_text):
        
        # 1. Define Tools
        @tool
        def job_search_tool(query: str):
            """Searches for job listings. Input example: 'Python Developer'."""
            return f"Found 3 listings for {query}: 1. Senior Role ($120k), 2. Junior Role ($80k)."

        @tool
        def salary_estimator(query: str):
            """Estimates salary. Input example: 'Data Scientist'."""
            return f"Estimated Salary range for {query}: $90k - $140k depending on experience."

        tools = [job_search_tool, salary_estimator]
        
        # 2. Initialize LLM (Must remove 'models/' prefix for LangChain)
        lc_model_name = self.working_model_name.replace("models/", "")
        llm = ChatGoogleGenerativeAI(
            model=lc_model_name,
            google_api_key=self.api_key,
            temperature=0.3
        )

        # 3. Create LangGraph Agent (The Fix)
        # LangGraph handles the prompt engineering internally for tool use
        system_message = f"""You are a helpful Career Assistant.
        You have access to the user's resume context below.
        
        RESUME CONTEXT:
        {resume_text}
        
        Answer the user's career questions using the tools provided if necessary.
        """
        
        try:
            # This creates a compiled graph that works exactly like the old agent
            agent_graph = create_react_agent(llm, tools, state_modifier=system_message)
            
            # 4. Invoke the Graph
            response = agent_graph.invoke({"messages": [HumanMessage(content=user_query)]})
            
            # Extract the final AI message content
            return response["messages"][-1].content
            
        except Exception as e:
            return f"Chat Error: {str(e)}"