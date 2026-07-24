# backend/ai_service.py
import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def generate_repo_insights(repo_name: str, owner: str, description: str, language: str) -> dict:
    """
    Uses Gemini 2.5 Flash with structured JSON output to return clean summaries and roadmaps.
    """
    if not client:
        return {
            "summary": description or "No description provided.",
            "roadmap": ["Add your GEMINI_API_KEY in backend/.env to unlock AI insights!"]
        }

    prompt = f"""
    You are an expert open-source mentor helping junior developers start contributing to GitHub projects.
    
    Analyze this repository:
    - Repository Name: {repo_name}
    - Owner: {owner}
    - Primary Language: {language}
    - Description: {description}
    
    Provide a JSON object with exactly two keys:
    1. "summary": A clear, 2-sentence plain English summary explaining what this project builds or solves.
    2. "roadmap": An array of 3 bullet points advising a beginner on how to start contributing to this codebase.
    """

    try:
        # Enforce pure JSON response structure from Gemini
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        # Parse Gemini's JSON string into a native Python dictionary
        insights_data = json.loads(response.text)
        return insights_data

    except Exception as e:
        return {
            "summary": description or "Unable to generate AI summary.",
            "roadmap": [f"AI analysis unavailable: {str(e)}"]
        }