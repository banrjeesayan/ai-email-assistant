import os
from dotenv import load_dotenv

# Load .env file from root or backend directory
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import AnalyzeEmailRequest, EmailAnalysisResult
from app.analyzer import analyze_email
from app.sample_data import SAMPLE_EMAILS

app = FastAPI(
    title="AI Executive Email Assistant API",
    description="Backend API for AI Email Analysis, Schema Validation, Prompt Injection Defense, and Evaluation Benchmarks.",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "AI Email Assistant API", "version": "1.0.0"}

@app.get("/api/samples")
def get_samples():
    """Return all sample emails for quick selection on the frontend."""
    return [
        {
            "id": s["id"],
            "category": s["category"],
            "title": s["title"],
            "difficulty": s["difficulty"],
            "email": s["email"],
            "ground_truth": s["ground_truth"]
        }
        for s in SAMPLE_EMAILS
    ]

@app.post("/api/analyze")
def analyze(req: AnalyzeEmailRequest):
    """Analyzes an incoming email using Gemini API or offline fallback engine."""
    try:
        result, source = analyze_email(req)
        return {
            "success": True,
            "execution_source": source,
            "data": result.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
