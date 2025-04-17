from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)


def create_db_and_tables() -> None:
    """Create all tables in the database."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get a session for the database.

    Returns:
        A generator of sessions for the database.
    """
    with Session(engine) as session:
        yield session
