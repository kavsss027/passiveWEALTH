import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.database.models.base import Base

@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    # create tables just in case, or assume they are created via migrations
    async with engine.begin() as conn:
        pass # migrations are already run by alembic
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(db_engine):
    SessionLocal = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with SessionLocal() as session:
        transaction = await session.begin()
        try:
            yield session
        finally:
            await transaction.rollback()
