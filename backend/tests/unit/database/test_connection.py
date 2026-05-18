import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db, engine, AsyncSessionLocal

@pytest.mark.asyncio
async def test_get_db_yields_session():
    async for session in get_db():
        assert isinstance(session, AsyncSession)
        break
