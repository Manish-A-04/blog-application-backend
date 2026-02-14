from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import settings
from app.routers import auth, users, blogs, comments, admin
from app.utils.scheduler import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown

app = FastAPI(title="Blog Application Backend", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(blogs.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Blog Application Backend"}
