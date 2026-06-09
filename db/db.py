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


def _clean_database_url(url: str) -> str:
    if "@" in url:
        credentials, host_db = url.rsplit("@", 1)
        if "#" in credentials:
            credentials = credentials.replace("#", "%23")
            url = f"{credentials}@{host_db}"
    return url


DATABASE_URL = _clean_database_url(_get_database_url())


# Create async engine with IPv4 resolution to prevent IPv6 timeout on Windows
def _create_engine():
    import socket
    import ssl
    from sqlalchemy.engine import make_url

    url = DATABASE_URL
    connect_args = {}

    if url.startswith("postgresql+asyncpg://"):
        try:
            url_obj = make_url(url)
            host = url_obj.host
            if host:
                # Resolve hostname to IPv4 to prevent IPv6 timeout issues in asyncio/Windows
                addr_info = socket.getaddrinfo(host, url_obj.port or 5432, family=socket.AF_INET)
                ipv4_ip = addr_info[0][4][0]
                url_obj = url_obj._replace(host=ipv4_ip)
                url = url_obj.render_as_string(hide_password=False)
                
                # Disable SSL hostname verification when connecting by IP address
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                connect_args["ssl"] = ctx
        except Exception:
            # Fallback to the original URL if resolution fails
            url = DATABASE_URL
            connect_args = {}

    return create_async_engine(url, connect_args=connect_args, echo=False)


# create async engine
engine = _create_engine()

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


