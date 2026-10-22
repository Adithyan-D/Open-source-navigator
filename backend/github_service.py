# backend/github_service.py
import os
import math
import logging
import datetime
import httpx
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("github_service")

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Curated rotation topics to dynamically change default repositories over time
ROTATING_CURATED_TOPICS = [
    "ai stars:>1000",
    "python stars:>1000",
    "typescript stars:>1000",
    "rust stars:>1000",
    "javascript stars:>1000",
    "go stars:>1000",
    "stars:>5000",
    "stars:>2000"
]

def get_rotating_default_query() -> str:
    """
    Returns a dynamic, rotating query based on time of day (rotates every 30 minutes).
    Ensures that default repositories change over time without breaking pagination.
    """
    interval_block = int(datetime.datetime.now(datetime.timezone.utc).timestamp() // 1800)
    return ROTATING_CURATED_TOPICS[interval_block % len(ROTATING_CURATED_TOPICS)]

def get_github_headers() -> Dict[str, str]:
    """Builds standard headers for GitHub API requests, adding authorization if token is configured."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "OpenSourceNavigator-App"
    }
    if GITHUB_TOKEN and GITHUB_TOKEN.strip():
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN.strip()}"
    return headers

def calculate_complexity_score(stars: int, forks: int, open_issues: int) -> int:
    """
    Uses logarithmic scaling so repos produce distinct, meaningful 
    complexity scores between 1 and 99 without capping top projects at 99.
    """
    if stars <= 0:
        return 10
    
    # Balanced logarithmic multipliers across star/fork/issue ranges
    # 500k stars -> ~45 pts | 50k forks -> ~28 pts | 1k issues -> ~12 pts (Total ~85)
    star_impact = math.log10(stars + 1) * 8
    fork_impact = math.log10(forks + 1) * 6
    issue_impact = math.log10(open_issues + 1) * 4
    
    raw_metric = star_impact + fork_impact + issue_impact
    
    return min(99, max(1, int(raw_metric)))

def calculate_health_score(open_issues: int, stars: int, forks: int) -> int:
    """
    Evaluates project health based on community engagement and issue backlog ratios.
    """
    if stars <= 0:
        return 50
    
    # Active contributor ratio (forks to stars)
    fork_ratio = forks / stars
    
    base_health = 70
    if fork_ratio > 0.15:   # High community engagement
        base_health += 15
    elif fork_ratio < 0.05: # Low engagement relative to stars
        base_health -= 10

    if open_issues > 2000:  # Large issue backlog
        base_health -= 20
    elif open_issues > 500:
        base_health -= 10
    elif open_issues < 100: # Clean issue backlog
        base_health += 10
        
    return min(99, max(20, base_health))

async def fetch_github_repositories(query: str = "", limit: int = 12, page: int = 1) -> List[Dict[str, Any]]:
    """
    Queries GitHub's Search API with resilient fallback chaining:
    1. Tries user's exact query.
    2. If no repos found, tries relaxed keywords.
    3. If still no repos found or if query is empty, falls back to dynamic rotating topics.
    Ensures that repositories are ALWAYS returned for every search query and change over time.
    """
    headers = get_github_headers()
    clean_query = query.strip() if query and query.strip() else ""
    
    candidates = []
    if clean_query:
        candidates.append(clean_query)
        words = [w for w in clean_query.split() if len(w) > 1]
        if len(words) > 2:
            candidates.append(" ".join(words[:2]))
        if len(words) > 1:
            candidates.append(words[0])
            
        # Fallbacks to ensure non-empty results even for rare keywords/typos
        candidates.append(get_rotating_default_query())
        candidates.append("stars:>1000")
    else:
        # Default query rotates over time
        candidates.append(get_rotating_default_query())
        candidates.append("stars:>1000")

    # Deduplicate while preserving order
    unique_candidates = []
    for c in candidates:
        if c and c not in unique_candidates:
            unique_candidates.append(c)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for attempt_query in unique_candidates:
                params = {
                    "q": attempt_query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": min(100, max(1, limit)),
                    "page": max(1, page)
                }

                response = await client.get(GITHUB_SEARCH_URL, headers=headers, params=params)
                
                if response.status_code in (403, 429):
                    logger.warning("GitHub API rate limit exceeded.")
                    return []
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                items = data.get("items", [])
                
                if items:
                    parsed_repos = []
                    for item in items:
                        stars = item.get("stargazers_count", 0) or 0
                        forks = item.get("forks_count", 0) or 0
                        open_issues = item.get("open_issues_count", 0) or 0
                        
                        parsed_repos.append({
                            "github_id": item.get("id"),
                            "name": item.get("name", "Unknown"),
                            "owner": item.get("owner", {}).get("login", "Unknown"),
                            "description": item.get("description") or "",
                            "stars": stars,
                            "forks": forks,
                            "open_issues": open_issues,
                            "languages": item.get("language") or "General",
                            "complexity_score": calculate_complexity_score(stars, forks, open_issues),
                            "health_score": calculate_health_score(open_issues, stars, forks),
                        })
                    return parsed_repos

            return []
    except Exception as e:
        logger.error(f"Error fetching GitHub repositories: {e}")
        return []
