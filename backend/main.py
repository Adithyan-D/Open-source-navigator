import github_service
import ai_service
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from database import engine, get_db
import models
import schemas
import auth

# Synchronize database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Open Source Navigator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Open Source Navigator API!",
        "status": "Database tables synchronized successfully."
    }

@app.post("/api/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. Check if the email already exists in the database
    existing_email = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )

    # 2. Check if the username already exists
    existing_username = db.query(models.User).filter(models.User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken."
        )

    # 3. Hash the plain text password securely using bcrypt
    hashed_password = auth.get_password_hash(user_data.password)

    # 4. Create a new User model instance
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )

    # 5. Save the user to our Neon Postgres database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Refreshes the instance to get the auto-generated ID from the DB

    # FastAPI will automatically filter this through schemas.UserResponse 
    # to make sure the hashed_password is never sent back to the client!
    return new_user

@app.post("/api/login", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    # 1. Fetch user by username
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    
    # 2. Verify user exists and password is correct
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Create JWT token storing user ID and username
    access_token = auth.create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )

    # 4. Return token
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
    
    db.commit()
    db.refresh(current_user)
    return current_user

@app.get("/api/recommendations", response_model=list[schemas.RepositoryResponse])
async def get_repository_recommendations(
    query: Optional[str] = None,
    page: int = 1,  # <-- Added pagination support
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Fetches GitHub repositories matched to the authenticated user's skills,
    interests, or active search queries, complete with custom complexity and health scores.
    """
    search_query = ""

    # Priority 1: User explicitly typed something in the frontend search bar or onboarding modal
    if query and query.strip():
        search_query = query.strip()

    # Priority 2: Fall back to the user's saved database skills
    elif current_user.skills and current_user.skills.strip():
        primary_skill = current_user.skills.split(",")[0].strip()
        search_query = primary_skill

    # Priority 3: Fall back to general trending/popular repositories
    else:
        search_query = "stars:>1000"

    # Fetch processed repositories from GitHub service with pagination
    repos = await github_service.fetch_github_repositories(
        query=search_query, 
        limit=12, 
        page=page
    )
    
    return repos

@app.post("/api/bookmarks/{github_id}", response_model=schemas.RepositoryResponse)
async def bookmark_repository(
    github_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Saves a repository to the user's bookmarks."""
    # 1. Check if the repo is already in our local Postgres/SQLite table
    repo = db.query(models.Repository).filter(models.Repository.github_id == github_id).first()

    # 2. If not indexed in local DB yet, fetch details from GitHub REST API
    if not repo:
        import httpx
        url = f"https://api.github.com/repositories/{github_id}"
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "OpenSourceNavigator-App"}
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=404, detail="GitHub repository not found.")
            
            item = resp.json()
            stars = item.get("stargazers_count", 0) or 0
            forks = item.get("forks_count", 0) or 0
            open_issues = item.get("open_issues_count", 0) or 0
            
            # Save repo record to database
            repo = models.Repository(
                github_id=item.get("id"),
                name=item.get("name", "Unknown"),
                owner=item.get("owner", {}).get("login", "Unknown"),
                description=item.get("description") or "",
                stars=stars,
                forks=forks,
                open_issues=open_issues,
                languages=item.get("language") or "Unknown",
                complexity_score=github_service.calculate_complexity_score(stars, forks, open_issues),
                health_score=github_service.calculate_health_score(open_issues, stars, forks),
            )
            db.add(repo)
            db.commit()
            db.refresh(repo)

    # 3. Check if user already bookmarked this repo
    existing_bookmark = db.query(models.Bookmark).filter(
        models.Bookmark.user_id == current_user.id,
        models.Bookmark.repository_id == repo.id
    ).first()

    if existing_bookmark:
        raise HTTPException(status_code=400, detail="Repository already bookmarked.")

    # 4. Save new bookmark relation
    new_bookmark = models.Bookmark(user_id=current_user.id, repository_id=repo.id)
    db.add(new_bookmark)
    db.commit()
    
    return repo


@app.get("/api/bookmarks", response_model=list[schemas.RepositoryResponse])
def get_user_bookmarks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Retrieves all repositories bookmarked by the authenticated user."""
    bookmarks = db.query(models.Bookmark).filter(models.Bookmark.user_id == current_user.id).all()
    return [b.repository for b in bookmarks]

@app.post("/api/repositories/{github_id}/ai-insights", response_model=schemas.AIInsightsResponse)
async def get_repository_ai_insights(
    github_id: int,
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Generates AI-powered repository insights using Gemini for a given GitHub repo.
    """
    import httpx
    url = f"https://api.github.com/repositories/{github_id}"
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "OpenSourceNavigator-App"}
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=404, detail="GitHub repository not found.")
        
        data = resp.json()
        
        # Call AI service
        insights = ai_service.generate_repo_insights(
            repo_name=data.get("name", ""),
            owner=data.get("owner", {}).get("login", ""),
            description=data.get("description", ""),
            language=data.get("language", "Unknown")
        )
        
        return {
            "github_id": github_id,
            "repo_name": data.get("name"),
            "ai_insights": insights
        }