import sys
import os


# Add parent folder to path so Python can find rag_system
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from rag_system.query_subject import ask_question  # Import after setting sys.path

# Initialize FastAPI app
app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8506"],  # ✅ Your Streamlit app URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "EduBot backend is running 🎓"}

@app.post("/ask")
async def ask_api(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"error": "❌ No JSON data received in the request."}

    question = data.get("question")
    subject = data.get("subject")

    if not question or not subject:
        return {"answer": "❗ Please provide both subject and question."}

    result = ask_question(subject, question)
    return {"answer": result}

