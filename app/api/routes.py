import logging
import time
from datetime import date, timezone

import httpx
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.sql.expression import cast
from sqlalchemy.types import Date

from app.api.dependencies import SessionDep
from app.api.schemas import AllStatsResponse, DailyCount, WeeklyStatsResponse
from app.core.config import settings
from app.core.models import Reaction as ReactionDB
from app.core.models import UserMessage as UserMessageDB
from app.core.schemas import ReactionResponse, ReactionUpdate, UserMessage

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/user_messages", response_model=UserMessage)
async def create_user_message(user_message: UserMessage, session: SessionDep):
    stmt = select(UserMessageDB).where(
        UserMessageDB.message_id == user_message.message_id
    )
    start = time.monotonic()
    result = await session.execute(stmt)
    logger.info("Executed user message check query in %.3f seconds", time.monotonic() - start)

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
        start = time.monotonic()
        await session.commit()
        logger.info("Committed new user message in %.3f seconds", time.monotonic() - start)

        start = time.monotonic()
        await session.refresh(user_message_db)
        logger.info("Refreshed new user message in %.3f seconds", time.monotonic() - start)

        return user_message_db
    except Exception as e:
        await session.rollback()
        logger.exception(
            "Database error during user message creation for message_id %s: %s",
            user_message.message_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
        )


@router.get("/user_messages/best", response_model=int)
async def get_best_message(session: SessionDep, today: date):
    stmt = (
        select(ReactionDB)
        .join(UserMessageDB, UserMessageDB.message_id == ReactionDB.message_id)
        .where(func.date(UserMessageDB.created_at) == today)
    )
    start = time.monotonic()
    result = await session.execute(stmt)
    logger.info("Executed best message query in %.3f seconds", time.monotonic() - start)

    reactions = result.scalars().all()
    if not reactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reactions found for today",
        )

    message_reaction_sums = {
        reaction.message_id: sum(r.get("total_count", 0) for r in reaction.reactions)
        for reaction in reactions
    }
    logger.info("Message reaction sums %s for date %s", message_reaction_sums, today)

    return max(message_reaction_sums, key=lambda x: message_reaction_sums[x])


@router.get("/user_messages/{message_id}", response_model=UserMessage)
async def get_user_message(message_id: int, session: SessionDep):
    start = time.monotonic()
    db_message = await session.get(UserMessageDB, message_id)
    logger.info("Fetched user message %s in %.3f seconds", message_id, time.monotonic() - start)

    if db_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User message not found",
        )
    return db_message


@router.delete("/user_messages/{message_id}")
async def delete_user_message(message_id: int, session: SessionDep):
    start = time.monotonic()
    db_message = await session.get(UserMessageDB, message_id)
    db_reaction = await session.get(ReactionDB, message_id)
    logger.info("Fetched message and reaction for deletion in %.3f seconds", time.monotonic() - start)

    if db_message is None and db_reaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User message and reaction not found",
        )
    try:
        if db_message is not None:
            await session.delete(db_message)
        if db_reaction is not None:
            await session.delete(db_reaction)

        start = time.monotonic()
        await session.commit()
        logger.info("Committed deletion in %.3f seconds", time.monotonic() - start)
    except Exception as e:
        await session.rollback()
        logger.exception(
            "Database error during deletion for message_id %s: %s",
            message_id,
            e,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed",
        )


@router.put("/reactions", response_model=ReactionResponse)
async def update_reaction(reaction_update: ReactionUpdate, session: SessionDep):
    stmt = select(ReactionDB).where(ReactionDB.message_id == reaction_update.message_id)
    start = time.monotonic()
    result = await session.execute(stmt)
    logger.info("Executed reaction select in %.3f seconds", time.monotonic() - start)

    db_log = result.scalar_one_or_none()

    if db_log:
        if db_log.changed_at.replace(tzinfo=timezone.utc) > reaction_update.changed_at:
            logger.info(
                "Skipping reaction update for message_id %s: new update is older",
                reaction_update.message_id,
            )
            return db_log

        logger.info("Updating existing reaction log for message_id %s", reaction_update.message_id)
        db_log.changed_at = reaction_update.changed_at
        db_log.reactions = [r.model_dump(mode="json") for r in reaction_update.reactions]
        session.add(db_log)
    else:
        logger.info("Creating new reaction log for message_id %s", reaction_update.message_id)
        db_log = ReactionDB(
            message_id=reaction_update.message_id,
            changed_at=reaction_update.changed_at,
            reactions=[r.model_dump(mode="json") for r in reaction_update.reactions],
        )
        session.add(db_log)

    try:
        start = time.monotonic()
        await session.commit()
        logger.info("Committed reaction update in %.3f seconds", time.monotonic() - start)

        start = time.monotonic()
        await session.refresh(db_log)
        logger.info("Refreshed reaction log in %.3f seconds", time.monotonic() - start)

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
    start = time.monotonic()
    db_log = await session.get(ReactionDB, message_id)
    logger.info("Fetched reaction log %s in %.3f seconds", message_id, time.monotonic() - start)

    if db_log is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reaction log not found",
        )
    return db_log
