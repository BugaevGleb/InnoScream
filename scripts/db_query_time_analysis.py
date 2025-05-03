import random  # noqa
import timeit
from datetime import datetime, timedelta, timezone  # noqa
from pathlib import Path

from sqlalchemy import (
    JSON,
    DateTime,
    Integer,
    String,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import (
    Mapped,
    Session,
    declarative_base,
    mapped_column,
    sessionmaker,
)

NUMBER_OF_REPEATS = 1000

engine = create_engine(
    f"sqlite:///{Path(__file__).parent.parent / 'db.sqlite3'}",
    echo=False,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, class_=Session
)
session = SessionLocal()

Base = declarative_base()


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


def get_user_message_by_message_id(message_id: int) -> None:
    """Get a user message by its message ID."""
    stmt = select(UserMessage).where(UserMessage.message_id == message_id)
    result = session.execute(stmt)
    result.scalar_one_or_none()


def get_best_message() -> None:
    """Get the best message of the day."""
    today = datetime.now(timezone.utc).date()
    stmt = (
        select(Reaction)
        .join(
            UserMessage,
            UserMessage.message_id == Reaction.message_id,
        )
        .where(func.date(UserMessage.created_at) == today)
    )
    result = session.execute(stmt)
    result.scalars().all()


def get_reaction_by_message_id(message_id: int) -> None:
    """Get a reaction by its message ID."""
    stmt = select(Reaction).where(Reaction.message_id == message_id)
    result = session.execute(stmt)
    result.scalar_one_or_none()


def get_count_of_messages_by_date(
    start_datetime_utc: datetime, end_datetime_utc: datetime
) -> None:
    """Get the count of messages by date."""
    stmt = select(func.count(UserMessage.message_id)).where(
        UserMessage.created_at >= start_datetime_utc,
        UserMessage.created_at < end_datetime_utc,
    )
    result = session.execute(stmt)
    result.scalar_one_or_none()


def get_all_time_daily_stats() -> None:
    """Get the count of messages by date for all time."""
    date_col = func.date(UserMessage.created_at).label("date")
    stmt = (
        select(
            date_col,
            func.count(UserMessage.message_id).label("count"),
        )
        .group_by(date_col)
        .order_by(date_col)
    )
    result = session.execute(stmt)
    result.all()


def get_user_stats(user_id: str) -> None:
    """Get the count of messages by user ID."""
    stmt = (
        select(func.count())
        .select_from(UserMessage)
        .where(UserMessage.user_id == user_id)
    )
    result = session.execute(stmt)
    result.scalar_one_or_none()


for func_name, query in (
    (
        "get_user_message_by_message_id",
        "get_user_message_by_message_id(random.randint(0, 300))",
    ),
    ("get_best_message", "get_best_message()"),
    (
        "get_reaction_by_message_id",
        "get_reaction_by_message_id(random.randint(0, 300))",
    ),
    (
        "get_count_of_messages_by_date",
        (
            "get_count_of_messages_by_date(datetime.now(timezone.utc), "
            "datetime.now(timezone.utc) + timedelta(days=1))"
        ),
    ),
    ("get_all_time_daily_stats", "get_all_time_daily_stats()"),
    ("get_user_stats", "get_user_stats(random.randint(0, 300))"),
):
    print(f"{func_name}")
    total = timeit.timeit(
        query,
        number=NUMBER_OF_REPEATS,
        globals=globals(),
    )
    print(
        (
            f"Average time for {NUMBER_OF_REPEATS} queries: "
            f"{total / NUMBER_OF_REPEATS * 1000:.3f} milliseconds"
        )
    )
    print()
