# backend/schemas.py
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ProfileUpdate(BaseModel):
    skills: str
    interests: str

class RepositoryResponse(BaseModel):
    github_id: int
    name: str
    owner: str
    description: Optional[str] = None
    stars: int
    forks: int
    open_issues: int
    languages: str
    complexity_score: Optional[int] = None
    health_score: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class AIInsightsData(BaseModel):
    summary: str
    roadmap: List[str]

class AIInsightsResponse(BaseModel):
    github_id: int
    repo_name: str
    ai_insights: AIInsightsData
