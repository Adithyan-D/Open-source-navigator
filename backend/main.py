# backend/main.py
import os
import logging
from typing import Optional, List
import httpx
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv

import models
import schemas
import auth
import github_service
import ai_service
from database import engine, get_db

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Synchronize database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Open Source Navigator API",
    description="Intelligent recommendations and developer onboarding for open-source repositories.",
    version="1.0.0"
)

# Parse CORS allowed origins from environment variable
raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"
)
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Open Source Navigator API!",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint to verify API and database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status
    }

@app.post("/api/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if email already registered
    existing_email = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )

    # 2. Check if username already taken
    existing_username = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken."
        )

    # 3. Hash plain password securely
    hashed_password = auth.get_password_hash(user_data.password)

    # 4. Create and commit new user
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user."
        )

@app.post("/api/login", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # 1. Fetch user by username
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    # 2. Verify credentials
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Create access token
    access_token = auth.create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/profile", response_model=schemas.UserResponse)
def get_user_profile(current_user: models.User = Depends(auth.get_current_user)):
    """Returns the currently logged-in user's profile details."""
    return current_user

@app.put("/api/profile", response_model=schemas.UserResponse)
def update_user_profile(
    profile_data: schemas.ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Updates skills and interests for the authenticated user."""
    current_user.skills = profile_data.skills
    current_user.interests = profile_data.interests
    
    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile."
        )

@app.get("/api/recommendations", response_model=List[schemas.RepositoryResponse])
async def get_repository_recommendations(
    query: Optional[str] = None,
    page: int = 1,
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Fetches GitHub repositories matched to the authenticated user's skills,
    interests, or active search queries, complete with custom complexity and health scores.
    """
    search_query = ""

    # Priority 1: User explicitly searched in the frontend
    if query and query.strip():
        search_query = query.strip()

    # Priority 2: Fall back to the user's primary saved skill
    elif current_user.skills and current_user.skills.strip():
        primary_skill = current_user.skills.split(",")[0].strip()
        search_query = primary_skill

    # Priority 3: Fall back to general popular repositories
    else:
        search_query = "stars:>1000"

    repos = await github_service.fetch_github_repositories(
        query=search_query, 
        limit=12, 
        page=max(1, page)
    )
    
    return repos

@app.post("/api/bookmarks/{github_id}", response_model=schemas.RepositoryResponse)
async def bookmark_repository(
    github_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Saves a repository to the user's bookmarks."""
    # 1. Check if repo is already indexed in our local table
    repo = db.query(models.Repository).filter(models.Repository.github_id == github_id).first()

    # 2. If not indexed yet, fetch repo metadata from GitHub REST API
    if not repo:
        url = f"https://api.github.com/repositories/{github_id}"
        headers = github_service.get_github_headers()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 404:
                    raise HTTPException(status_code=404, detail="GitHub repository not found.")
                elif resp.status_code in (403, 429):
                    raise HTTPException(status_code=429, detail="GitHub API rate limit exceeded. Please try again later.")
                elif resp.status_code != 200:
                    raise HTTPException(status_code=502, detail="Failed to fetch repository from GitHub.")
                
                item = resp.json()
                stars = item.get("stargazers_count", 0) or 0
                forks = item.get("forks_count", 0) or 0
                open_issues = item.get("open_issues_count", 0) or 0
                
                repo = models.Repository(
                    github_id=item.get("id"),
                    name=item.get("name", "Unknown"),
                    owner=item.get("owner", {}).get("login", "Unknown"),
                    description=item.get("description") or "",
                    stars=stars,
                    forks=forks,
                    open_issues=open_issues,
                    languages=item.get("language") or "General",
                    complexity_score=github_service.calculate_complexity_score(stars, forks, open_issues),
                    health_score=github_service.calculate_health_score(open_issues, stars, forks),
                )
                db.add(repo)
                db.commit()
                db.refresh(repo)
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error fetching/saving repository {github_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal error bookmarking repository.")

    # 3. Check if user already bookmarked this repo
    existing_bookmark = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == current_user.id,
        models.Bookmark.repository_id == repo.id
    ).first()

    if existing_bookmark:
        raise HTTPException(status_code=400, detail="Repository already bookmarked.")

    # 4. Save bookmark relation
    new_bookmark = models.Bookmark(user_id=current_user.id, repository_id=repo.id)
    try:
        db.add(new_bookmark)
        db.commit()
        return repo
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving bookmark for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save bookmark.")

@app.get("/api/bookmarks", response_model=List[schemas.RepositoryResponse])
def get_user_bookmarks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Retrieves all repositories bookmarked by the authenticated user."""
    bookmarks = db.query(models.Bookmark).filter(models.Bookmark.user_id == current_user.id).all()
    return [b.repository for b in bookmarks if b.repository is not None]

@app.post("/api/repositories/{github_id}/ai-insights", response_model=schemas.AIInsightsResponse)
async def get_repository_ai_insights(
    github_id: int,
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Generates AI-powered repository insights using Gemini for a given GitHub repo.
    """
    url = f"https://api.github.com/repositories/{github_id}"
    headers = github_service.get_github_headers()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="GitHub repository not found.")
            elif resp.status_code in (403, 429):
                raise HTTPException(status_code=429, detail="GitHub API rate limit exceeded. Please try again later.")
            elif resp.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to retrieve repository from GitHub.")
            
            data = resp.json()
            
            insights = ai_service.generate_repo_insights(
                repo_name=data.get("name", ""),
                owner=data.get("owner", {}).get("login", ""),
                description=data.get("description", ""),
                language=data.get("language", "General")
            )
            
            return {
                "github_id": github_id,
                "repo_name": data.get("name"),
                "ai_insights": insights
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating AI insights for {github_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI insights.")
