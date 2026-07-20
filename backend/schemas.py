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
    