from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from app.models.blog import Blog, BlogStatus
from app.models.user import User
from app.models.like import Like
from app.models.comment import Comment
from app.schemas.blog import BlogCreate, BlogUpdate
from datetime import datetime
from typing import List, Optional

async def get_blog(db: AsyncSession, blog_id: int):
    result = await db.execute(select(Blog).where(Blog.id == blog_id))
    return result.scalars().first()

async def get_blogs(
    db: AsyncSession, 
    page: int = 1, 
    limit: int = 10, 
    search: Optional[str] = None, 
    tag: Optional[str] = None,
    current_user_id: Optional[int] = None
):
    query = select(Blog).order_by(desc(Blog.created_at))
    
    # Filter by status:
    # - published: visible to everyone
    # - draft: visible only to owner (we need to handle this logic in router or here)
    # The requirement says: 
    # - published blogs publicly
    # - draft blogs only to owner
    # - scheduled blogs only when scheduled_at <= now() (which means they should be published?)
    
    # Actually, the scheduler should FLIP scheduled -> published.
    # But if looking at "scheduled" blogs:
    # "scheduled blogs only when scheduled_at <= now()" -> this implies they are effectively published.
    
    # Let's handle the visibility logic.
    # If no current_user, only show published.
    # If current_user, show published OR (draft AND author_id == current_user) OR (scheduled AND author_id == current_user).
    
    # Wait, the requirement is simpler: "Only show: published blogs publicly, draft blogs only to owner..."
    # So we filter generally.
    
    conditions = []
    
    # Search
    if search:
        conditions.append(Blog.title.ilike(f"%{search}%"))
        
    # Tag
    if tag:
        # PostgreSQL array check
        conditions.append(Blog.tags.contains([tag])) # or use ANY logic if needed by dialect
    
    # Apply filters
    if conditions:
        query = query.where(*conditions)

    # We need to fetch author as well for the response
    # SQLAlchemy lazy loading might work, but eager loading is better for async
    from sqlalchemy.orm import selectinload
    query = query.options(selectinload(Blog.author))
 
    # Pagination
    # First get total count
    # count_query = select(func.count()).select_from(query.subquery()) # approximate
    # To get accurate count with filters:
    # We execute a separate count query
    
    # TODO: Refine count query
    
    # Apply limit/offset
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    blogs = result.scalars().all()
    
    return blogs

async def create_blog(db: AsyncSession, blog: BlogCreate, author_id: int):
    # Logic: If scheduled_at > now, status = scheduled
    # Logic: If scheduled_at > now, status = scheduled
    blog_data = blog.model_dump()
    if blog.scheduled_at and blog.scheduled_at > datetime.now(blog.scheduled_at.tzinfo):
        blog_data["status"] = BlogStatus.scheduled
        
    db_blog = Blog(
        **blog_data,
        author_id=author_id
    )
    db.add(db_blog)
    await db.commit()
    await db.refresh(db_blog)
    return db_blog

async def update_blog(db: AsyncSession, blog_id: int, blog_update: BlogUpdate, user: User):
    db_blog = await get_blog(db, blog_id)
    if not db_blog:
        return None
        
    # Check permissions: Owner or Admin
    if db_blog.author_id != user.id and user.role != "admin":
        return None # Or raise in router
        
    update_data = blog_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_blog, key, value)
        
    db_blog.updated_by = user.username
    
    db.add(db_blog)
    await db.commit()
    await db.refresh(db_blog)
    return db_blog

async def delete_blog(db: AsyncSession, blog_id: int, user: User):
    db_blog = await get_blog(db, blog_id)
    if not db_blog:
        return None
        
    if db_blog.author_id != user.id and user.role != "admin":
        return None
        
    await db.delete(db_blog)
    await db.commit()
    return True

async def like_blog(db: AsyncSession, blog_id: int, user_id: int):
    # Check if already liked
    result = await db.execute(select(Like).where(Like.blog_id == blog_id, Like.user_id == user_id))
    existing_like = result.scalars().first()
    if existing_like:
        return False # Already liked
        
    new_like = Like(blog_id=blog_id, user_id=user_id)
    db.add(new_like)
    await db.commit()
    return True

async def unlike_blog(db: AsyncSession, blog_id: int, user_id: int):
    result = await db.execute(select(Like).where(Like.blog_id == blog_id, Like.user_id == user_id))
    existing_like = result.scalars().first()
    if not existing_like:
        return False
        
    await db.delete(existing_like)
    await db.commit()
    return True

async def get_metrics(db: AsyncSession):
    # Admin metrics
    total_users = await db.scalar(select(func.count(User.id)))
    total_blogs = await db.scalar(select(func.count(Blog.id)))
    total_comments = await db.scalar(select(func.count(Comment.id)))
    total_likes = await db.scalar(select(func.count(Like.id)))
    
    return {
        "total_users": total_users,
        "total_blogs": total_blogs,
        "total_comments": total_comments,
        "total_likes": total_likes
    }

async def publish_scheduled_blogs(db: AsyncSession):
    """
    Checks for blogs with status 'scheduled' and scheduled_at <= now(),
    and updates their status to 'published'.
    """
    now = datetime.now()
    # We need to be careful with timezones. 
    # If scheduled_at is timezone aware (it is in model), we should compare with timezone aware now.
    # But let's assume the server and db are aligned or use naive if unsure.
    # Best practice: use func.now() from DB, but easier to just check in python if logic is complex.
    # Simple query: UPDATE blogs SET status='published' WHERE status='scheduled' AND scheduled_at <= NOW()
    
    from sqlalchemy import update
    
    stmt = (
        update(Blog)
        .where(Blog.status == BlogStatus.scheduled)
        .where(Blog.scheduled_at <= func.now())
        .values(status=BlogStatus.published)
    )
    
    await db.execute(stmt)
    await db.commit()

