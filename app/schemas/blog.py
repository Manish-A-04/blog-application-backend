from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from datetime import datetime
from app.models.blog import BlogStatus
from app.schemas.user import UserOut

# --- Comment Schemas ---
class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    pass

class CommentOut(CommentBase):
    id: int
    blog_id: int
    user_id: int
    created_at: datetime
    created_at: datetime
    author: UserOut = Field(..., alias="user") # Map user relationship to author field

    class Config:
        from_attributes = True

# --- Blog Schemas ---
class BlogBase(BaseModel):
    title: str
    description: Optional[str] = None
    content: str
    cover_image: Optional[str] = None
    tags: List[str] = []
    status: BlogStatus = BlogStatus.draft
    scheduled_at: Optional[datetime] = None

class BlogCreate(BlogBase):
    pass

class BlogUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    cover_image: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[BlogStatus] = None
    scheduled_at: Optional[datetime] = None

class BlogOut(BlogBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[str] = None
    likes_count: int = 0
    comments_count: int = 0
    author: UserOut # Nested author details

    class Config:
        from_attributes = True

class BlogListResponse(BaseModel):
    total: int
    page: int
    limit: int
    blogs: List[BlogOut]

class BlogDetail(BlogOut):
    content: str # content is already in BlogBase, but confirm it's needed here. BlogOut has it.
    comments: List[CommentOut] = []
    is_liked: bool = False
