# backend/ai_service.py
import os
import json
import logging
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ai_service")

# Initialize Gemini Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY and GEMINI_API_KEY.strip() else None

def generate_repo_insights(repo_name: str, owner: str, description: str, language: str) -> dict:
    """
    Uses Gemini with structured JSON output to return clean summaries and roadmaps for open source repositories.
    """
    fallback_summary = description or "No description provided by repository maintainer."
    
    if not client:
        return {
            "summary": fallback_summary,
            "roadmap": [
                "Configure GEMINI_API_KEY in backend/.env to unlock AI-powered summaries and custom contribution roadmaps.",
                f"Explore repository documentation and read the README at https://github.com/{owner}/{repo_name}.",
                "Check open issues labeled 'good first issue' or 'help wanted' to make your first contribution."
            ]
        }

    prompt = f"""
    You are an expert open-source mentor helping developers start contributing to GitHub projects.
    
    Analyze this repository:
    - Repository Name: {repo_name}
    - Owner: {owner}
    - Primary Language: {language}
    - Description: {description}
    
    Provide a JSON object with exactly two keys:
    1. "summary": A clear, 2-sentence plain English summary explaining what this project builds or solves.
    2. "roadmap": An array of exactly 3 concise, actionable bullet points advising a beginner on how to understand and start contributing to this codebase.
    """

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        raw_text = response.text.strip()
        
        # Clean any potential markdown fencing if present
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text)
            raw_text = re.sub(r"\n?```$", "", raw_text)
            
        insights_data = json.loads(raw_text)
        
        # Validate expected keys
        if "summary" in insights_data and "roadmap" in insights_data:
            return insights_data
            
        return {
            "summary": insights_data.get("summary", fallback_summary),
            "roadmap": insights_data.get("roadmap", ["Review repository documentation to get started."])
        }

    except Exception as e:
        logger.error(f"Error generating AI repo insights with Gemini: {e}")
        return {
            "summary": fallback_summary,
            "roadmap": [
                f"Explore project codebase at https://github.com/{owner}/{repo_name}.",
                "Inspect setup steps in README and run the application locally.",
                "Browse open issues labeled 'good first issue' to submit your first pull request."
            ]
        }
