
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.blog import Blog
from app.models.user import User
import os
from dotenv import load_dotenv

load_dotenv(r"C:\Users\hp\Desktop\blog\backend\.env")

DATABASE_URL = os.getenv("DATABASE_URL")
if "postgresql://" in DATABASE_URL and "postgresql+asyncpg://" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async def check_ownership():
    engine = create_async_engine(DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as db:
        print("\n--- Users ---")
        users = await db.scalars(select(User))
        user_map = {}
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}, Role: {user.role}")
            user_map[user.id] = user.username

        print("\n--- Blogs ---")
        blogs = await db.scalars(select(Blog))
        for blog in blogs:
             author_name = user_map.get(blog.author_id, "Unknown")
             print(f"B:{blog.id}|{blog.status}|uid:{blog.author_id}|{author_name}")

if __name__ == "__main__":
    asyncio.run(check_ownership())
