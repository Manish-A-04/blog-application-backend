# Blog Application Backend

A robust FastAPI backend for a modern blog application, featuring user authentication, blog management, scheduling, and admin controls.

## Tech Stack

-   **Framework**: FastAPI
-   **Database**: PostgreSQL (Async with `asyncpg`)
-   **ORM**: SQLAlchemy (Async)
-   **Authentication**: JWT (JSON Web Tokens)
-   **Migrations**: Alembic
-   **Scheduler**: APScheduler (for background tasks)
-   **Validation**: Pydantic

## Features

-   **User Authentication**: Register, Login, JWT-based protected routes.
-   **Blog Management**: Create, Read, Update, Delete (CRUD) blogs.
-   **Blog Scheduling**: Schedule posts to be published automatically at a future date.
-   **Lazy Publishing**: Automatically publishes scheduled posts when users visit the site.
-   **Comments & Likes**: Interactive features for readers.
-   **Admin Dashboard API**: Endpoints for analytics and content management.
-   **Tag System**: Categorize posts with tags.
-   **Neon/AWS Ready**: Configured for deployment on modern cloud infrastructure.

## Setup

1.  **Clone the repository**
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Environment Variables**:
    Create a `.env` file in the `backend` directory with the following:
    ```env
    DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
    SECRET_KEY=your_secret_key_here
    ALGORITHM=HS256
    ACCESS_TOKEN_EXPIRE_MINUTES=30
    ```
    *Note: If using Neon, the system automatically handles the SSL connection.*

5.  **Run Migrations**:
    ```bash
    alembic upgrade head
    ```

6.  **Create Admin User**:
    Run the interactive script to create a superuser:
    ```bash
    python create_admin.py
    ```

## Running the Server

**Development**:
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`.
Docs are at `http://localhost:8000/docs`.

**Production**:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```
