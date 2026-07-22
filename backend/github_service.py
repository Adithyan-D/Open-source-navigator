# backend/github_service.py
import httpx
import math
from typing import List, Dict, Any

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

def calculate_complexity_score(stars: int, forks: int, open_issues: int) -> int:
    """
    Uses logarithmic scaling so repos with 1,000 vs 100,000 stars 
    produce distinct, meaningful scores between 1 and 99.
    """
    if stars <= 0:
        return 10
    
    # Logarithmic impact: scales smoothly across huge variations in star/fork counts
    raw_metric = (math.log10(stars + 1) * 15) + (math.log10(forks + 1) * 10) + (math.log10(open_issues + 1) * 5)
    
    return min(99, max(1, int(raw_metric)))

def calculate_health_score(open_issues: int, stars: int, forks: int) -> int:
    """
    Evaluates project health based on community engagement and manageable issue loads.
    """
    if stars <= 0:
        return 50
    
    # Active contributor ratio (forks to stars)
    fork_ratio = forks / stars
    
    # Calculate balance score
    base_health = 70
    if fork_ratio > 0.15:   # High community engagement/forks
        base_health += 15
    if open_issues > 1000: # High issue backlog
        base_health -= 15
    elif open_issues < 100:
        base_health += 10
        
    return min(99, max(20, base_health))

async def fetch_github_repositories(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Queries GitHub's Search API for public repositories matching the user's keywords or language.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "OpenSourceNavigator-App"
    }
    
    # Construct search query (e.g., language:python sort by stars)
    params = {
        "q": query if query else "stars:>100",
        "sort": "stars",
        "order": "desc",
        "per_page": limit
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(GITHUB_SEARCH_URL, headers=headers, params=params)
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            items = data.get("items", [])
            
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
                    "languages": item.get("language") or "Unknown",
                    "complexity_score": calculate_complexity_score(stars, forks, open_issues),
                    "health_score": calculate_health_score(open_issues, stars, forks),
                })
                
            return parsed_repos
        except Exception:
            # Prevents server crashes if GitHub API times out or fails
            return []