from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.comment import Comment
from app.models.user import User, UserRole
from app.core.deps import get_current_user

router = APIRouter(prefix="/comments", tags=["comments"])

@router.delete("/{id}")
async def delete_comment(
    id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(Comment).where(Comment.id == id))
    comment = result.scalars().first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
        
    # User can delete own, Admin can delete any
    if comment.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    await db.delete(comment)
    await db.commit()
    return {"detail": "Comment deleted"}
