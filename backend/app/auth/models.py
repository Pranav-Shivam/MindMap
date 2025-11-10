"""
User models for authentication.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class User(BaseModel):
    """User model."""
    id: str = Field(alias="_id")
    email: EmailStr
    created_at: datetime
    
    class Config:
        populate_by_name = True


class UserCreate(BaseModel):
    """User registration model."""
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """User login model."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response model (without password)."""
    id: str
    email: str
    created_at: str


class Token(BaseModel):
    """Token model."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[str] = None
    email: Optional[str] = None

