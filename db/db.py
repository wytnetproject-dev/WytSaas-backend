from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Base(DeclarativeBase):
    pass


def _get_database_url() -> str:
    raw = os.environ.get("DATABASE_URL")
    if not raw:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. Expected format: 'postgresql+asyncpg://user:pass@host:port/dbname'"
        )
    # strip surrounding quotes and whitespace
    url = raw.strip().strip('"').strip("'")
    # common typo: postgres+asyncpg -> postgresql+asyncpg
    if url.startswith("postgres+asyncpg:"):
        url = url.replace("postgres+asyncpg:", "postgresql+asyncpg:", 1)

    # basic validation
    if not url.startswith("postgresql+asyncpg://") and not url.startswith("sqlite:") and not url.startswith("postgresql://"):
        raise RuntimeError(f"DATABASE_URL looks malformed: {url}")

    return url


DATABASE_URL = _get_database_url()

# create async engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Use the new async_sessionmaker instead
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with async_session() as session:
        try:
            yield session
            # await session.commit()
        except Exception:
            await session.rollback()
            raise


