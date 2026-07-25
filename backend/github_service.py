# backend/github_service.py
import httpx
import math
from typing import List, Dict, Any

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

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

async def fetch_github_repositories(query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Queries GitHub's Search API for public repositories matching keywords or languages.
    """
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "OpenSourceNavigator-App"
    }
    
    # Use specified query or fallback to top starred repos
    search_query = query.strip() if query and query.strip() else "stars:>100"
    
    params = {
        "q": search_query,
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
                    "languages": item.get("language") or "General",
                    "complexity_score": calculate_complexity_score(stars, forks, open_issues),
                    "health_score": calculate_health_score(open_issues, stars, forks),
                })
                
            return parsed_repos
        except Exception:
            return []