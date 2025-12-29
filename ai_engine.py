import json
import random
import math
import time
from PIL import ImageDraw, ImageFont

# NATIVE SDK
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import ResourceExhausted, InternalServerError

# REAL SEARCH
try:
    from duckduckgo_search import DDGS
except ImportError:
    print("⚠️ 'duckduckgo-search' not installed. Using fallback.")
    DDGS = None

from utils import image_to_base64

class CareerAIEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
        # Tools
        self.tools = [self.job_search_tool]
        
        # Force Discovery
        self.model_name = self._get_valid_model_name()
        print(f"✅ Engine Locked on: {self.model_name}")

    def _get_valid_model_name(self):
        try:
            models = list(genai.list_models())
            model_names = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            priorities = ["gemini-1.5-flash", "gemini-1.5-pro"]
            for p in priorities:
                for name in model_names:
                    if p in name: return name
            if model_names: return model_names[0]
            return "models/gemini-1.5-flash"
        except:
            return "models/gemini-1.5-flash"

    # --- REAL JOB SEARCH TOOL ---
    def job_search_tool(self, query: str):
        """Searches for REAL job listings using DuckDuckGo."""
        if not DDGS:
            return "Error: duckduckgo-search library missing. Please install it."
            
        print(f"🔎 Searching web for: {query}...")
        try:
            with DDGS() as ddgs:
                # Search for recent results (past month)
                results = list(ddgs.text(f"{query} jobs hiring now", max_results=5, timelimit='m'))
                
            if not results:
                return "No specific listings found right now."
                
            # Format results
            formatted = "Here are some real listings found:\n"
            for i, res in enumerate(results, 1):
                formatted += f"{i}. {res['title']} - {res['href']}\n"
            return formatted
            
        except Exception as e:
            return f"Search failed: {str(e)}"

    # --- VISION ENGINE ---
    def analyze_resume_vision(self, image):
        prompt = """
        You are a Senior Technical Recruiter grading a resume with a Red Pen.
        Identify 3-4 CRITICAL flaws (e.g., generic text, missing impact, bad formatting).
        Return ONLY a JSON object:
        { "critiques": [ { "type": "circle", "x": 50, "y": 20, "comment": "Quantify this!" } ] }
        Constraint: 'x' and 'y' are percentages (0-100).
        """
        
        safety = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        # RETRY LOGIC
        max_retries = 3
        last_error = "Unknown Error"
        
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content([prompt, image], safety_settings=safety)
                content = response.text.replace("```json", "").replace("```", "").strip()
                if "{" in content:
                    content = content[content.find("{"):content.rfind("}")+1]
                return json.loads(content)
            
            except ResourceExhausted:
                last_error = "Quota Exceeded (429). Please wait a moment."
                time.sleep(10) 
            except Exception as e:
                last_error = str(e)
                if "finish_reason" in str(e).lower():
                    return {"error": "Safety Block: Resume content flagged."}
                time.sleep(1)

        return {"error": f"Failed after {max_retries} attempts. Last error: {last_error}"}

    def draw_red_pen(self, image, annotations):
        if "error" in annotations: return image
        if not annotations or "critiques" not in annotations: return image
        
        overlay = image.convert("RGB")
        draw = ImageDraw.Draw(overlay)
        width, height = overlay.size
        
        font_size = int(height * 0.015)
        try: font = ImageFont.truetype("arial.ttf", font_size)
        except: font = ImageFont.load_default()

        critiques = sorted(annotations["critiques"], key=lambda k: k['y'])
        occupied_zones = []

        for item in critiques:
            cx, cy = (item['x'] / 100) * width, (item['y'] / 100) * height
            r_x, r_y = width * 0.15, height * 0.05
            
            self._draw_rough_circle(draw, cx, cy, r_x/2, r_y/2)
            
            text = f"--> {item['comment']}"
            tx = cx + r_x/2 + 20
            max_text_width = width - tx - 20
            
            if max_text_width < 150:
                 tx = 20
                 max_text_width = (cx - r_x/2) - 40
            
            lines = self._get_wrapped_lines(draw, text, font, max_text_width)
            line_height = draw.textbbox((0, 0), "Tg", font=font)[3] - draw.textbbox((0, 0), "Tg", font=font)[1] + 5
            total_block_height = len(lines) * line_height
            
            ty = cy - 10 
            collision = True
            loop_guard = 0
            while collision and loop_guard < 10:
                collision = False
                current_bottom = ty + total_block_height
                for (occ_top, occ_bottom) in occupied_zones:
                    if (ty < occ_bottom) and (current_bottom > occ_top):
                        ty = occ_bottom + 10
                        collision = True
                        break
                loop_guard += 1

            occupied_zones.append((ty, ty + total_block_height))
            
            for i, line in enumerate(lines):
                cur_y = ty + (i * line_height)
                self._draw_text_with_outline(draw, (tx, cur_y), line, font, (180, 0, 0), (255, 255, 255))
                
            if abs(ty - cy) > 50:
                 draw.line([(cx, cy + r_y/2), (tx, ty)], fill=(200, 0, 0, 100), width=1)

        return overlay

    def _get_wrapped_lines(self, draw, text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        return lines

    def _draw_rough_circle(self, draw, cx, cy, rx, ry):
        points = []
        steps = 40
        for i in range(steps + 1):
            angle = (i / steps) * 2 * math.pi
            noise_x = random.uniform(-0.05, 0.05) * rx
            noise_y = random.uniform(-0.05, 0.05) * ry
            x = cx + (rx + noise_x) * math.cos(angle)
            y = cy + (ry + noise_y) * math.sin(angle)
            points.append((x, y))
        draw.line(points, fill=(200, 0, 0, 220), width=3, joint="curve")

    def _draw_text_with_outline(self, draw, pos, text, font, text_color, outline_color):
        x, y = pos
        for adj in [-2, 0, 2]:
            for adj2 in [-2, 0, 2]:
                draw.text((x+adj, y+adj2), text, font=font, fill=outline_color)
        draw.text((x, y), text, font=font, fill=text_color)

    # --- CHAT ENGINE ---
    def start_chat_session(self, resume_text):
        system_instruction = f"""You are an expert Career Consultant.
        RESUME CONTEXT:
        {resume_text}
        
        CRITICAL INSTRUCTIONS:
        1. **SALARY:** Do NOT use tools. Use internal knowledge based on user location.
        2. **JOB SEARCH:** Use job_search_tool ONLY if specifically asked for listings.
        """
        model = genai.GenerativeModel(
            model_name=self.model_name,
            tools=self.tools,
            system_instruction=system_instruction
        )
        return model.start_chat(enable_automatic_function_calling=True)

    def run_chat(self, chat_session, user_query):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = chat_session.send_message(user_query)
                return response.text
            except ResourceExhausted:
                time.sleep(5)
            except Exception as e:
                return f"Chat Error: {str(e)}"
        return "⚠️ Server busy. Please wait a minute."