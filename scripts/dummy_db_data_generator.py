import random
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    JSON,
    DateTime,
    Integer,
    String,
    create_engine,
    delete,
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

engine = create_engine(
    f"sqlite:///{Path(__file__).parent.parent / 'db.sqlite3'}",
    echo=False,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, class_=Session
)

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


NUM_ROWS_TO_GENERATE = 300

print("Creating tables if they don't exist...")
Base.metadata.create_all(bind=engine)
print("Tables checked/created.")

print("\nAbout to delete existing data from user_messages and reactions.")
print("Press Enter to continue or Ctrl+C to abort...")
input()

with SessionLocal() as session:
    print("Deleting existing data...")
    session.execute(delete(Reaction))
    session.execute(delete(UserMessage))
    session.commit()
    print("Existing data deleted.")

    print(f"\nInserting {NUM_ROWS_TO_GENERATE} rows into user_messages...")
    messages_to_add = []
    for i in range(NUM_ROWS_TO_GENERATE):
        msg = UserMessage(
            message_id=i,
            user_id=str(random.randint(1, 50)),
            message=f"Test {i}",
            created_at=datetime.now(timezone.utc),
        )
        messages_to_add.append(msg)
    session.add_all(messages_to_add)
    session.commit()
    print("User messages inserted.")

    user_message_count = session.execute(
        select(func.count(UserMessage.message_id))
    ).scalar_one()
    print(f"Rows now in user_messages table: {user_message_count}")

    print(f"\nInserting {NUM_ROWS_TO_GENERATE} rows into reactions...")
    reactions_to_add = []
    for i in range(NUM_ROWS_TO_GENERATE):
        reaction = Reaction(
            message_id=i,
            changed_at=datetime.now(timezone.utc),
            reactions=[
                {f"emoji_{j}": random.randint(1, 100)}
                for j in range(random.randint(1, 3))
            ],
        )
        reactions_to_add.append(reaction)
    session.add_all(reactions_to_add)
    session.commit()
    print("Reactions inserted.")

    reaction_count = session.execute(
        select(func.count(Reaction.message_id))
    ).scalar_one()
    print(f"Rows now in reactions table: {reaction_count}")

print("\nData generation complete.")
