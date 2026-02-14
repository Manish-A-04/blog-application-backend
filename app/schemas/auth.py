from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: UserRole = UserRole.user

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None

class UserOut(UserBase):
    id: int
    avatar_url: Optional[str] = None
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class RegisterResponse(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    access_token: str
    token_type: str
    
    class Config:
        from_attributes = True

class TokenData(BaseModel):
    username: Optional[str] = None
