import logging
from datetime import date, datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.sql.expression import cast

from app.api.dependencies import SessionDep
from app.api.schemas import AllStatsResponse, DailyCount, WeeklyStatsResponse
from app.core.config import settings
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


@router.get("/user_messages/best", response_model=int)
async def get_best_message(session: SessionDep, today: date):
    """Retrieve the message id with the most reactions from the database."""
    stmt = (
        select(ReactionDB)
        .join(
            UserMessageDB,
            UserMessageDB.message_id == ReactionDB.message_id,
        )
        .where(func.date(UserMessageDB.created_at) == today)
    )
    result = await session.execute(stmt)
    reactions = result.scalars().all()
    if not reactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reactions found for today",
        )

    message_reaction_sums = {
        reaction.message_id: sum(
            r.get("total_count", 0) for r in reaction.reactions
        )
        for reaction in reactions
    }
    logger.info(
        "Message reaction sums %s for date %s", message_reaction_sums, today
    )

    return max(message_reaction_sums, key=message_reaction_sums.get)


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


@router.delete("/user_messages/{message_id}")
async def delete_user_message(message_id: int, session: SessionDep):
    """Delete a user message by message ID."""
    db_message = await session.get(UserMessageDB, message_id)
    db_reaction = await session.get(ReactionDB, message_id)
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
        await session.commit()
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
        if (
            db_log.changed_at.replace(tzinfo=timezone.utc)
            > reaction_update.changed_at
        ):
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


@router.get("/stats/daily/{target_date_str}", response_model=int)
async def get_daily_stats(target_date_str: str, session: SessionDep):
    """Get the number of messages posted on a specific date (YYYY-MM-DD)."""
    logger.info("Fetching stats for specific date: %s", target_date_str)

    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except ValueError:
        logger.error("Invalid date format provided: %s", target_date_str)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD.",
        )

    try:
        start_datetime_utc = datetime.combine(
            target_date, datetime.time.min, tzinfo=datetime.timezone.utc
        )
        end_datetime_utc = start_datetime_utc + datetime.timedelta(days=1)
        logger.info(
            "Querying count from %s to %s",
            start_datetime_utc,
            end_datetime_utc,
        )
    except Exception as e:
        logger.exception("Error creating date boundaries: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating date boundaries",
        )

    try:
        stmt = select(func.count(UserMessageDB.message_id)).where(
            UserMessageDB.created_at >= start_datetime_utc,
            UserMessageDB.created_at < end_datetime_utc,
        )
        result = await session.execute(stmt)
        count = result.scalar_one_or_none() or 0

        logger.info("Count for %s: %s", target_date_str, count)
        return count

    except Exception as e:
        logger.exception(
            "Database error fetching stats for %s: %s", target_date_str, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database query failed",
        )


@router.get("/stats/weekly", response_model=WeeklyStatsResponse)
async def get_weekly_stats_via_daily():
    """Get weekly stats by calling the daily stats endpoint \
    for the last 7 days."""
    logger.info("Fetching weekly stats via daily endpoint calls...")
    response_stats = []

    try:
        now_utc = datetime.now(datetime.timezone.utc)
        today_utc = now_utc.date()
        all_dates = [
            today_utc - datetime.timedelta(days=i) for i in range(6, -1, -1)
        ]  # Past 6 days + today
    except Exception as e:
        logger.exception(
            "Error calculating date range for weekly stats: %s", e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error calculating date range",
        )

    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
        for current_date in all_dates:
            date_str = current_date.strftime("%Y-%m-%d")
            logger.info("Fetching stats for date: %s", date_str)
            daily_url = f"{settings.INNOSCREAM_API_URL}/stats/daily/{date_str}"
            count = 0
            try:
                response = await client.get(daily_url)
                response.raise_for_status()
                count = response.json()
                logger.debug(
                    "Successfully fetched count for %s: %s", date_str, count
                )
            except httpx.HTTPStatusError as e:
                logger.warning(
                    "HTTP error calling daily stats for %s: %s - %s",
                    date_str,
                    e.response.status_code,
                    e.response.text,
                )
            except Exception as e:
                logger.exception(
                    "Error calling daily stats for %s: %s", date_str, e
                )

            response_stats.append(
                DailyCount(day=current_date.strftime("%a"), count=count)
            )

    logger.info("Assembled weekly stats: %s", response_stats)
    return WeeklyStatsResponse(stats=response_stats)


@router.get("/stats/all", response_model=AllStatsResponse)
async def get_all_time_stats(session: SessionDep):
    """Get the number of messages posted per day for all time."""
    logger.info("Fetching all-time daily stats...")

    stmt = (
        select(
            cast(UserMessageDB.created_at, func.date()).label("date"),
            func.count(UserMessageDB.message_id).label("count"),
        )
        .group_by(cast(UserMessageDB.created_at, func.date()))
        .order_by(cast(UserMessageDB.created_at, func.date()))
    )

    result = await session.execute(stmt)
    daily_counts_db = result.all()

    response_stats = [
        DailyCount(day=db_date.strftime("%Y-%m-%d"), count=count)
        for db_date, count in daily_counts_db
    ]

    logger.info("All-time stats result count: %s", len(response_stats))
    return AllStatsResponse(stats=response_stats)


@router.get("/stats/{user_id}", response_model=int)
async def get_user_stats(user_id: str, session: SessionDep):
    """Get the total number of messages posted by a specific user."""
    stmt = (
        select(func.count())
        .select_from(UserMessageDB)
        .where(UserMessageDB.user_id == user_id)
    )
    result = await session.execute(stmt)
    count = result.scalar_one_or_none()

    if count is None:
        logger.warning("Count for user_id %s returned None.", user_id)
        return 0

    return count
