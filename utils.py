import io
import base64
from pdf2image import convert_from_bytes
import PyPDF2

def convert_pdf_to_image(file_bytes):
    try:
        images = convert_from_bytes(file_bytes, dpi=200)
        return images[0] if images else None
    except Exception as e:
        print(f"Image Error: {e}")
        return None

def extract_text_from_pdf(file_bytes):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content: text += content + "\n"
            
        # --- CRITICAL FIX: SANITIZE TEXT ---
        # This removes "surrogate" characters that crash the Google API
        # by forcing a clean UTF-8 encoding/decoding cycle.
        clean_text = text.encode('utf-8', 'ignore').decode('utf-8')
        return clean_text

    except Exception as e:
        print(f"Text Error: {e}")
        return ""

def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"