import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import (
    get_db_session,
    create_db_and_tables,
    engine,
    Base,
)


@pytest.mark.asyncio
async def test_create_db_and_tables():
    """Test table creation does not raise exceptions."""
    try:
        await create_db_and_tables()
    except Exception as e:
        pytest.fail(f"create_db_and_tables failed: {e}")


@pytest.mark.asyncio
async def test_get_db_session():
    """Test get_db_session yields a valid AsyncSession."""
    async for session in get_db_session():
        assert isinstance(session, AsyncSession)
        break


def test_engine_creation():
    """Test SQLAlchemy engine is initialized."""
    assert "sqlite" in (
        str(engine.url) or str(engine.url).startswith("postgres"))
    assert engine is not None


def test_base_metadata():
    """Test declarative base metadata."""
    assert hasattr(Base, "metadata")
