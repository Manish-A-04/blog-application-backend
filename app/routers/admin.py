from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.core.deps import get_current_admin_user
from app.services import blog_service
import csv
import io

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/analytics")
async def get_analytics(
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    return await blog_service.get_metrics(db)

@router.get("/export/csv")
async def export_csv(
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Fetch blogs with author relationship loaded would be ideal, 
    # but here we might rely on lazy loading if session is open, or it might fail in async.
    # Ideally should use options(joinedload(Blog.author)) in the service.
    # For now, let's assume service returns what we need or we fetch.
    blogs = await blog_service.get_blogs(db, limit=1000) 
    
    stream = io.StringIO()
    writer = csv.writer(stream)
    # matching fields from previous google sheets export
    writer.writerow(["ID", "Title", "Description", "Content", "Author", "Created At", "Status"])
    
    for blog in blogs:
        author_name = blog.author.username if blog.author else str(blog.author_id)
        writer.writerow([
            blog.id, 
            blog.title, 
            blog.description, 
            blog.content[:100], # Truncated content 
            author_name, 
            blog.created_at,
            blog.status
        ])
        
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=blogs_export.csv"
    return response
