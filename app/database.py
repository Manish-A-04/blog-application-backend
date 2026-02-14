from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Handle Neon/Render postgres:// protocol
db_url = settings.DATABASE_URL
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url and db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Configure engine with SSL if needed (Neon usually requires it)
connect_args = {}
if "neon.tech" in db_url or "aws.com" in db_url:
    connect_args = {"ssl": "require"}

engine = create_async_engine(
    db_url, 
    echo=True,
    connect_args=connect_args,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(autoflush=False, class_=AsyncSession, expire_on_commit=False, bind=engine)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
