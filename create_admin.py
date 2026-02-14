import asyncio
import sys
import getpass
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from sqlalchemy import select

async def create_admin():
    print("--- Create Admin User ---")
    username = input("Enter admin username: ").strip()
    email = input("Enter admin email: ").strip()
    
    while True:
        password = getpass.getpass("Enter admin password: ")
        confirm_password = getpass.getpass("Confirm password: ")
        
        if password == confirm_password and password:
            break
        print("Passwords do not match or are empty. Please try again.")

    async with AsyncSessionLocal() as db:
        # Check if exists
        result = await db.execute(select(User).where(User.username == username))
        existing_user = result.scalars().first()
        
        if existing_user:
            print(f"User '{username}' already exists.")
            return

        result_email = await db.execute(select(User).where(User.email == email))
        existing_email = result_email.scalars().first()
        
        if existing_email:
            print(f"Email '{email}' is already registered.")
            return

        print(f"Creating admin user '{username}'...")
        hashed_password = get_password_hash(password)
        
        new_admin = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            role=UserRole.admin
        )
        
        db.add(new_admin)
        await db.commit()
        print(f"Admin user '{username}' created successfully.")

if __name__ == "__main__":
    # Ensure app modules are found
    import os
    sys.path.append(os.getcwd())
    
    try:
        asyncio.run(create_admin())
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
