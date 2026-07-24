# backend/schemas.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    skills: str
    interests: str

    class Config:
        from_attributes = True

# --- NEW SCHEMAS FOR LOGIN & TOKENS ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class ProfileUpdate(BaseModel):
    skills: str
    interests: str

class RepositoryResponse(BaseModel):
    github_id: int
    name: str
    owner: str
    description: str | None = None
    stars: int
    forks: int
    open_issues: int
    languages: str
    complexity_score: int | None = None
    health_score: int | None = None

    class Config:
        from_attributes = True

# backend/schemas.py (Add at the bottom)

class AIInsightsData(BaseModel):
    summary: str
    roadmap: list[str]

class AIInsightsResponse(BaseModel):
    github_id: int
    repo_name: str
    ai_insights: AIInsightsData
    