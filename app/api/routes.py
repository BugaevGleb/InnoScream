import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.dependencies import SessionDep
from app.core.models import (
    Reaction as ReactionDB,
)
from app.core.models import (
    UserMessage as UserMessageDB,
)
from app.core.schemas import ReactionResponse, ReactionUpdate, UserMessage

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/user_messages", response_model=UserMessage)
async def create_user_message(user_message: UserMessage, session: SessionDep):
    """Create a new user message in the database."""
    stmt = select(UserMessageDB).where(
        UserMessageDB.message_id == user_message.message_id
    )
    result = await session.execute(stmt)
    db_message = result.scalar_one_or_none()
    if db_message:
        logger.info(
            "Skipping user message for message_id %s: message already exists",
            user_message.message_id,
        )
        return db_message

    user_message_db = UserMessageDB(
        message_id=user_message.message_id,
        user_id=user_message.user_id,
        message=user_message.message,
        created_at=user_message.created_at,
    )
    session.add(user_message_db)

    try:
        await session.commit()
        await session.refresh(user_message_db)
        return user_message_db
    except Exception as e:
        await session.rollback()
        logger.exception(
            (
                "Database error during user message creation "
                "for message_id %s: %s"
            ),
            user_message.message_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
        )


@router.get("/user_messages/{message_id}", response_model=UserMessage)
async def get_user_message(message_id: int, session: SessionDep):
    """Get a user message by message ID."""
    db_message = await session.get(UserMessageDB, message_id)
    if db_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User message not found",
        )
    return db_message


@router.put("/reactions", response_model=ReactionResponse)
async def update_reaction(
    reaction_update: ReactionUpdate, session: SessionDep
):
    """Update or create the reaction count log for a message in the database.

    If the reaction update is older than the existing reaction, it will be
    skipped.
    """
    stmt = select(ReactionDB).where(
        ReactionDB.message_id == reaction_update.message_id
    )
    result = await session.execute(stmt)
    db_log = result.scalar_one_or_none()

    if db_log:
        if db_log.changed_at > reaction_update.changed_at:
            logger.info(
                "Skipping reaction update for message_id %s: "
                "new reaction update is older than the existing one",
                reaction_update.message_id,
            )
            return db_log
        logger.info(
            "Updating existing reaction log for message_id %s",
            reaction_update.message_id,
        )
        db_log.changed_at = reaction_update.changed_at
        db_log.reactions = [
            r.model_dump(mode="json") for r in reaction_update.reactions
        ]
        session.add(db_log)
    else:
        logger.info(
            "Creating new reaction log for message_id %s",
            reaction_update.message_id,
        )
        db_log = ReactionDB(
            message_id=reaction_update.message_id,
            changed_at=reaction_update.changed_at,
            reactions=[
                r.model_dump(mode="json") for r in reaction_update.reactions
            ],
        )
        session.add(db_log)

    try:
        await session.commit()
        await session.refresh(db_log)
        return db_log
    except Exception as e:
        await session.rollback()
        logger.exception(
            "Database error during reaction update for message_id %s: %s",
            reaction_update.message_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
        )


@router.get("/reactions/{message_id}", response_model=ReactionResponse)
async def get_reaction_log(message_id: int, session: SessionDep):
    """Retrieve a specific reaction log by message ID."""
    db_log = await session.get(ReactionDB, message_id)
    if db_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reaction not found",
        )
    return db_log
