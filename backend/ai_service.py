# backend/ai_service.py
import os
import json
import logging
import re
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("ai_service")

# Default to gemini-3.8-flash as requested
DEFAULT_MODEL = "gemini-3.8-flash"
FALLBACK_MODELS = ["gemini-3.8-flash"]

class RepoInsightsSchema(BaseModel):
    summary: str = Field(description="A clear 2-sentence summary of what this project does and its core architecture")
    roadmap: List[str] = Field(description="Exactly 3 specific, actionable steps for a beginner to contribute to this repo")

def get_gemini_client():
    """Dynamically initializes or refreshes the Gemini client using the latest environment variables."""
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        return None, []
    
    clean_key = api_key.strip().strip("'\"")
    configured_model = os.getenv("GEMINI_MODEL", "").strip()

    models_to_try = []
    # If a specific valid model is set, use it; otherwise default to gemini-3.8-flash
    if configured_model and configured_model not in ("gemini-1.5-flash", "gemini-2.5-flash", "gemini-1.5-pro"):
        models_to_try.append(configured_model)
    else:
        models_to_try.append(DEFAULT_MODEL)
    
    for m in FALLBACK_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    try:
        client = genai.Client(api_key=clean_key)
        return client, models_to_try
    except Exception as e:
        logger.error(f"Failed to create Gemini client: {e}")
        return None, []

def generate_repo_insights(repo_name: str, owner: str, description: str, language: str) -> dict:
    """
    Uses Gemini 3.8 Flash with structured schema output to generate custom summaries and roadmaps.
    Fast response time (1-2s) by disabling thinking delay and expanding token limit to prevent truncation.
    """
    clean_desc = (description or "").strip()
    clean_lang = (language or "General").strip()
    fallback_summary = clean_desc if clean_desc else f"{repo_name} is an active open-source project written in {clean_lang}."
    
    fallback_roadmap = [
        f"Clone the repository from https://github.com/{owner}/{repo_name} and set up local {clean_lang} dependencies.",
        "Review the automated test suite and contributing guidelines to understand the codebase conventions.",
        f"Browse the issue tracker at https://github.com/{owner}/{repo_name}/issues to find starter issues."
    ]

    client, models_to_try = get_gemini_client()
    
    if not client or not models_to_try:
        return {
            "summary": fallback_summary,
            "roadmap": [
                "GEMINI_API_KEY is not configured in backend/.env.",
                "Generate an API key at https://aistudio.google.com/ and add it to backend/.env.",
                f"Explore repository documentation directly at https://github.com/{owner}/{repo_name}."
            ]
        }

    prompt = f"""You are an open-source technical mentor. Analyze this GitHub repository and generate beginner guidance:
- Repository: {repo_name}
- Maintainer: {owner}
- Language: {clean_lang}
- Description: {clean_desc or 'No description provided.'}

Provide:
1. summary: A clear 2-sentence summary explaining the problem this project solves and its core architecture.
2. roadmap: An array of exactly 3 distinct, tailored, actionable steps a new developer should take to start contributing to this specific codebase (e.g., local environment setup, running tests, picking beginner issues)."""

    last_error_msg = ""

    for model_name in models_to_try:
        try:
            # Build fast generation config:
            # thinking_budget=0 eliminates long reasoning delays (drops response time from minutes to 1-2s)
            # max_output_tokens=1024 prevents JSON truncation mid-string
            try:
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RepoInsightsSchema,
                    temperature=0.2,
                    max_output_tokens=1024,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                )
            except Exception:
                # Fallback if thinking_config or response_schema is not supported in the active environment
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                    max_output_tokens=1024,
                )

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config,
            )
            
            raw_text = (response.text or "").strip()
            
            # Clean potential markdown fencing
            if "```" in raw_text:
                raw_text = re.sub(r"^```[a-zA-Z]*\s*", "", raw_text)
                raw_text = re.sub(r"\s*```$", "", raw_text)
            
            # Extract JSON object substring if wrapped in any stray text
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                raw_text = json_match.group(0)

            insights_data = json.loads(raw_text)
            
            summary = insights_data.get("summary")
            roadmap = insights_data.get("roadmap")
            
            if summary and isinstance(roadmap, list) and len(roadmap) >= 2:
                return {
                    "summary": summary.strip(),
                    "roadmap": [step.strip() for step in roadmap if isinstance(step, str) and step.strip()]
                }
            elif summary:
                return {
                    "summary": summary.strip(),
                    "roadmap": fallback_roadmap
                }

        except Exception as e:
            last_error_msg = str(e)
            logger.warning(f"Model '{model_name}' attempt failed: {last_error_msg}")
            
            if "API_KEY_INVALID" in last_error_msg or "API key not valid" in last_error_msg:
                break
            elif "RESOURCE_EXHAUSTED" in last_error_msg or "429" in last_error_msg:
                break
            continue

    logger.error(f"All AI generation attempts failed. Last error: {last_error_msg}")
    
    if "API_KEY_INVALID" in last_error_msg or "API key not valid" in last_error_msg:
        return {
            "summary": fallback_summary,
            "roadmap": [
                "Invalid Gemini API Key: Your API key was rejected by Google AI Studio (API_KEY_INVALID).",
                "Please generate a new API key at https://aistudio.google.com/ and update GEMINI_API_KEY in backend/.env.",
                "No server restart required - after updating, click 'AI Insights' again."
            ]
        }
    elif "RESOURCE_EXHAUSTED" in last_error_msg or "429" in last_error_msg:
        return {
            "summary": fallback_summary,
            "roadmap": [
                "Gemini Quota Exceeded: The free-tier rate limit has been reached for this minute.",
                "Please wait 30 seconds and try clicking 'AI Insights' again.",
                f"You can also check open issues at https://github.com/{owner}/{repo_name}/issues."
            ]
        }
    else:
        # Graceful fallback: Never show raw JSON parse errors to recruiters or users
        return {
            "summary": fallback_summary,
            "roadmap": fallback_roadmap
        }
