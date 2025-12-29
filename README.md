# 🚀 RAG-Based Freelancer Assistant System

An AI-powered smart freelance platform that leverages **Google Gemini AI** and **RAG (Retrieval-Augmented Generation)** to provide intelligent resume analysis, career consulting, and real-time job search capabilities.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![Google Gemini](https://img.shields.io/badge/Google-Gemini_AI-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 📋 Table of Contents

- [Project Description](#-project-description)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Dependencies & Requirements](#-dependencies--requirements)
- [Setup Instructions](#-setup-instructions)
- [How to Run](#-how-to-run)
- [Usage Guide](#-usage-guide)
- [Team Members & Contributions](#-team-members--contributions)

---

## 📖 Project Description

The **RAG-Based Freelancer Assistant System** is an intelligent career platform designed to help freelancers and job seekers optimize their professional profiles. Built with cutting-edge AI technologies, this system provides:

- **Visual Resume Critique**: AI-powered analysis that identifies flaws in resume formatting, content, and presentation with "red pen" annotations
- **Career Consulting Chatbot**: Interactive AI assistant that answers career-related questions using context from the uploaded resume
- **Real-Time Job Search**: Integration with DuckDuckGo search to find relevant job listings based on user skills and preferences

The platform uses **Google Gemini AI** for natural language processing and vision capabilities, combined with **RAG architecture** to provide contextually relevant responses based on the user's resume content.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **PDF Resume Upload** | Upload and process PDF resumes with text extraction and image conversion |
| 🔍 **AI Visual Analysis** | Computer vision-based resume critique with annotated feedback |
| 💬 **Career Chatbot** | Context-aware AI assistant for career guidance and advice |
| 🔎 **Job Search** | Real-time job listing search using DuckDuckGo integration |
| 🎨 **Red Pen Annotations** | Visual markup showing areas for improvement on your resume |

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web Interface                   │
│                        (app.py)                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   PDF Upload  │  │  Visual AI   │  │  Chat Engine │       │
│  │   & Parser    │  │   Analysis   │  │   (RAG)      │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                  │                  │              │
├─────────────────────────────────────────────────────────────┤
│                    AI Engine (ai_engine.py)                  │
│  • Google Gemini Vision API                                  │
│  • Function Calling (Job Search Tool)                        │
│  • Conversation Management                                   │
├─────────────────────────────────────────────────────────────┤
│                    Utilities (utils.py)                      │
│  • PDF to Image Conversion                                   │
│  • Text Extraction (PyPDF2)                                  │
│  • Base64 Encoding                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Dependencies & Requirements

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Poppler**: Required for PDF to image conversion

### Python Packages

| Package | Purpose |
|---------|---------|
| `streamlit` | Web application framework |
| `python-dotenv` | Environment variable management |
| `langchain` | LLM framework |
| `langchain-community` | Community integrations |
| `langchain-google-genai` | Google Gemini integration |
| `google-generativeai` | Google Generative AI SDK |
| `faiss-cpu` | Vector similarity search |
| `PyPDF2` | PDF text extraction |
| `pdf2image` | PDF to image conversion |
| `Pillow` | Image processing |
| `duckduckgo-search` | Web search integration |

### External Requirements

- **Google API Key**: A valid Google Gemini API key is required

---

## 🛠 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/RAG-Based-Freelancer-assistant-System.git
cd RAG-Based-Freelancer-assistant-System
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

# Install DuckDuckGo search (optional, for job search feature)
pip install duckduckgo-search
```

### 4. Install Poppler (Required for PDF Processing)

**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get install poppler-utils
```

**Windows:**
- Download from: https://github.com/oschwartz10612/poppler-windows/releases
- Add the `bin` folder to your system PATH

### 5. Configure Environment Variables

Create a `.env` file in the project root directory:

```bash
# Create .env file
touch .env
```

Add your Google API key to the `.env` file:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

> 💡 **How to get a Google API Key:**
> 1. Go to [Google AI Studio](https://aistudio.google.com/)
> 2. Sign in with your Google account
> 3. Create a new API key
> 4. Copy and paste it into your `.env` file

---

## ▶️ How to Run

### Start the Application

```bash
streamlit run app.py
```

The application will launch in your default web browser at `http://localhost:8501`

### Alternative Run Methods

```bash
# Run on a specific port
streamlit run app.py --server.port 8080

# Run with auto-reload disabled
streamlit run app.py --server.runOnSave false
```

---

## 📱 Usage Guide

1. **Upload Resume**: Click "Upload PDF" in the sidebar to upload your resume
2. **Visual Analysis**: Click "🔍 Analyze Resume" to get AI-powered visual feedback with red pen annotations
3. **Chat with AI**: Use the chat interface to ask career questions like:
   - "What skills am I missing?"
   - "What is the expected salary for my profile?"
   - "Find me job listings for Python developers"
4. **Reset**: Click "Reset App" in the sidebar to start fresh with a new resume

---

## 👥 Team Members

| Name | Student ID |
|------|------------|
| **Youssef Hussieny** | 222101943 |
| **Adham Mohamed** | 222100195 |
| **Samaa Khaled** | 222100761 |
| **Habiba Ahmed** | 222100471 |

---

## 📁 Project Structure

```
RAG-Based-Freelancer-assistant-System/
├── app.py              # Main Streamlit application
├── ai_engine.py        # AI engine with Gemini integration
├── utils.py            # Utility functions for PDF processing
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (not in repo)
└── README.md           # Project documentation
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- Google Gemini AI for powering the intelligent analysis
- Streamlit for the amazing web framework
- LangChain for the RAG architecture support

---

