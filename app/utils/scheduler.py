from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import AsyncSessionLocal
from app.models.blog import Blog, BlogStatus
from datetime import datetime, timezone
import asyncio

scheduler = AsyncIOScheduler()

async def check_scheduled_blogs():
    print("Checking for scheduled blogs...")
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            # Find blogs that are scheduled and time has passed
            result = await db.execute(
                select(Blog)
                .where(
                    Blog.status == BlogStatus.scheduled,
                    Blog.scheduled_at <= now
                )
            )
            blogs_to_publish = result.scalars().all()
            
            if not blogs_to_publish:
                return

            for blog in blogs_to_publish:
                print(f"Publishing blog {blog.id}")
                blog.status = BlogStatus.published
                db.add(blog)
                
            await db.commit()
                    
        except Exception as e:
            print(f"Error in scheduler: {e}")
            await db.rollback()

def start_scheduler():
    scheduler.add_job(check_scheduled_blogs, 'interval', minutes=1)
    scheduler.start()
