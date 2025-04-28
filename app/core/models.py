import logging
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

logger = logging.getLogger(__name__)


class UserMessage(Base):
    """SQLAlchemy model for storing user messages."""

    __tablename__ = "user_messages"

    message_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    user_id: Mapped[str] = mapped_column(String)
    message: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)

    def __repr__(self):
        """Return a string representation of the UserMessage object."""
        return (
            f"<UserMessage(message_id={self.message_id}, "
            f"user_id={self.user_id}, created_at={self.created_at})>"
        )


class Reaction(Base):
    """SQLAlchemy model for storing message reaction updates."""

    __tablename__ = "reactions"

    message_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    changed_at: Mapped[datetime] = mapped_column(DateTime)
    reactions: Mapped[list[dict]] = mapped_column(JSON)

    def __repr__(self):
        """Return a string representation of the Reaction object."""
        return (
            f"<Reaction(message_id={self.message_id}, "
            f"changed_at={self.changed_at}, "
            f"reactions={self.reactions})>"
        )
