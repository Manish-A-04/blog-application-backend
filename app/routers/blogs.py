from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db
from app.models.user import User, UserRole
from app.models.blog import Blog, BlogStatus
# Ensure models are imported for relationships
from app.schemas.blog import BlogCreate, BlogUpdate, BlogOut, BlogListResponse, CommentCreate, CommentOut, BlogDetail
from app.models.comment import Comment
from app.models.like import Like
from app.services import blog_service
from app.core.deps import get_current_user, get_current_active_user
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/blogs", tags=["blogs"])



# Redefine logic for optional auth
from app.core.security import settings
from jose import jwt
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

async def get_optional_user(token: Annotated[str | None, Depends(oauth2_scheme_optional)], db: Annotated[AsyncSession, Depends(get_db)]):
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None: return None
    except:
        return None
        
    result = await db.execute(select(User).where(User.username == username))
    return result.scalars().first()

@router.get("", response_model=BlogListResponse)
async def read_blogs(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = 1,
    limit: int = 10,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_user)
):
    # Auto-publish scheduled blogs first
    await blog_service.publish_scheduled_blogs(db)

    query = select(Blog).order_by(desc(Blog.created_at))
    
    conditions = []
    if search:
        conditions.append(Blog.title.ilike(f"%{search}%"))
    if tag:
        conditions.append(Blog.tags.contains([tag]))

    # Visibility Logic
    # 1. Published: ALL can see
    # 2. Draft: Only Author can see
    # 3. Scheduled: Only Author can see (until published)
    
    if current_user:
        # Show (Published) OR (Draft/Scheduled AND Author is Me)
        # Note: Admin might see everything? "Only owner OR admin" was for update/delete. 
        # For list, let's assume Admin sees all too.
        if current_user.role == UserRole.admin:
            vis_condition = True # No filter
        else:
            vis_condition = (Blog.status == BlogStatus.published) | (Blog.author_id == current_user.id)
    else:
        vis_condition = (Blog.status == BlogStatus.published)

    if vis_condition is not True:
        query = query.where(vis_condition)
        
    if conditions:
        query = query.where(*conditions)
    
    # Check total count
    # (Simplified count for now, proper count needs subquery)
    # total = await db.scalar(select(func.count(Blog.id)).where(vis_condition)) 
    # We ideally run the same query structure for count.
    
    # Eager load author for response
    query = query.options(selectinload(Blog.author))
    
    # Count results (expensive but accurate)
    result_all = await db.execute(query)
    all_blogs = result_all.scalars().all()
    total = len(all_blogs)
    
    # Slice for pagination in memory (since we fetched all for count - not optimal for production but safe for logic)
    # Optimization: count query then limit query.
    start = (page - 1) * limit
    blogs_page = all_blogs[start : start + limit]
    
    # We also need likes_count and comments_count
    # Since they are not columns but computed or relationships, we can map them.
    # In Pydantic schema, we have likes_count.
    # We can use hybrid_property or just calculate here.
    # Let's use validation on return or simple attribute setting if model supports it.
    
    response_blogs = []
    for blog in blogs_page:

        # Simply:
        from app.models.like import Like
        from app.models.comment import Comment
        likes_count = await db.scalar(select(func.count()).where(Like.blog_id == blog.id))
        comments_count = await db.scalar(select(func.count()).where(Comment.blog_id == blog.id))
        
        blog.likes_count = likes_count
        blog.comments_count = comments_count
        response_blogs.append(blog)

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "blogs": response_blogs
    }

@router.get("/{id}", response_model=BlogDetail)
async def get_blog(
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Optional[User] = Depends(get_optional_user)
):
    # Fetch blog with relations
    # We need comments and their authors
    query = select(Blog).where(Blog.id == id).options(
        selectinload(Blog.author),
        selectinload(Blog.comments).selectinload(Comment.user)
    )
    result = await db.execute(query)
    blog = result.scalars().first()
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
        
    # Visibility Logic
    is_visible = False
    if blog.status == BlogStatus.published:
        is_visible = True
    elif current_user:
        if current_user.role == UserRole.admin or blog.author_id == current_user.id:
            is_visible = True
            
    if not is_visible:
        raise HTTPException(status_code=404, detail="Blog not found")

    # Counts & Extra Fields
    blog.comments_count = len(blog.comments)
    
    likes_count = await db.scalar(select(func.count()).where(Like.blog_id == id))
    blog.likes_count = likes_count
    
    blog.is_liked = False
    if current_user:
        user_like = await db.scalar(select(Like).where(
            (Like.blog_id == id) & (Like.user_id == current_user.id)
        ))
        if user_like:
            blog.is_liked = True
            
    return blog

@router.post("", response_model=BlogOut)
async def create_blog(
    blog: BlogCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if len(blog.tags) < 2:
        raise HTTPException(status_code=400, detail="Minimum 2 tags required")
        
    new_blog = await blog_service.create_blog(db, blog, current_user.id)
    # Reload with author
    # await db.refresh(new_blog, ["author"]) # Refresh with relation might fail if not loaded
    # Fetch again
    res = await db.execute(select(Blog).options(selectinload(Blog.author)).where(Blog.id == new_blog.id))
    new_blog_loaded = res.scalars().first()
    
    # Construct response with counts
    new_blog_loaded.likes_count = 0
    new_blog_loaded.comments_count = 0
    
    return new_blog_loaded

@router.put("/{id}", response_model=BlogOut)
async def update_blog(
    id: int,
    blog_update: BlogUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    updated = await blog_service.update_blog(db, id, blog_update, current_user)
    if not updated:
        raise HTTPException(status_code=403, detail="Not authorized or blog not found")
        
    res = await db.execute(select(Blog).options(selectinload(Blog.author)).where(Blog.id == id))
    updated_blog = res.scalars().first()
    
    # Calculate counts
    from app.models.like import Like
    from app.models.comment import Comment
    likes_count = await db.scalar(select(func.count()).where(Like.blog_id == id))
    comments_count = await db.scalar(select(func.count()).where(Comment.blog_id == id))
    
    updated_blog.likes_count = likes_count
    updated_blog.comments_count = comments_count
    
    return updated_blog

@router.delete("/{id}")
async def delete_blog(
    id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    success = await blog_service.delete_blog(db, id, current_user)
    if not success:
        raise HTTPException(status_code=403, detail="Not authorized or blog not found")
    return {"detail": "Blog deleted"}

# --- Likes ---
@router.post("/{id}/like")
async def like_blog(
    id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    await blog_service.like_blog(db, id, current_user.id)
    # Return updated count
    from app.models.like import Like
    count = await db.scalar(select(func.count()).where(Like.blog_id == id))
    return {"likes_count": count}

@router.delete("/{id}/like")
async def unlike_blog(
    id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    await blog_service.unlike_blog(db, id, current_user.id)
    from app.models.like import Like
    count = await db.scalar(select(func.count()).where(Like.blog_id == id))
    return {"likes_count": count}


# --- Comments ---
@router.post("/{id}/comments", response_model=CommentOut)
async def create_comment(
    id: int,
    comment: CommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    from app.models.comment import Comment
    new_comment = Comment(
        content=comment.content,
        blog_id=id,
        user_id=current_user.id
    )
    db.add(new_comment)
    await db.commit()
    await db.refresh(new_comment)
    return new_comment


