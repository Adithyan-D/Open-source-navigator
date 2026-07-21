# backend/models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, DateTime, func
from sqlalchemy.orm import relationship, declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    skills = Column(String, default="")
    interests = Column(String, default="") 
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    bookmarks = relationship("Bookmark", back_populates="user")


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    description = Column(String, nullable=True)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    open_issues = Column(Integer, default=0)
    languages = Column(String, default="")
    
    complexity_score = Column(Integer, nullable=True)
    health_score = Column(Integer, nullable=True)
    
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    bookmarks = relationship("Bookmark", back_populates="repository")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    status = Column(String, default="bookmarked")
    saved_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="bookmarks")
    repository = relationship("Repository", back_populates="bookmarks")
