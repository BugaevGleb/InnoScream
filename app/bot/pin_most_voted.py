import logging
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import AsyncSessionFactory
from app.core.models import (
    Reaction as ReactionDB,
)
from app.core.models import (
    UserMessage as UserMessageDB,
)

logger = logging.getLogger(__name__)


async def get_best_message_id():
    """Gets the best message ID from the database.

    Returns:
        int: The best message ID
    """
    today = datetime.now(timezone.utc).date()

    async with AsyncSessionFactory() as session:
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
            logger.info("No reactions found for today.")
            return None

        logger.info(f"Found {len(reactions)} reactions today.")

        message_reaction_sums = {
            reaction.message_id: sum(
                r.get("total_count", 0) for r in reaction.reactions
            )
            for reaction in reactions
        }
        logger.info(f"Message reaction sums: {message_reaction_sums}")

        best_message_id = max(
            message_reaction_sums, key=message_reaction_sums.get
        )

        logger.info(f"Best message_id selected: {best_message_id}")
        return best_message_id


async def pin_best_message(bot: Bot):
    """Pins the best message from the database.

    Args:
        bot: Bot instance
    """
    best_message_id = await get_best_message_id()
    if not best_message_id:
        logger.info("No messages to pin.")
        return

    try:
        await bot.pin_chat_message(
            chat_id=settings.INNOSCREAM_CHANNEL_ID,
            message_id=best_message_id,
            disable_notification=True,
        )
        logger.info(f"Pinned message {best_message_id} successfully.")
    except TelegramBadRequest as e:
        if "MESSAGE_ID_INVALID" in str(e):
            logger.warning(
                "Message %s not found or deleted. Removing from DB.",
                best_message_id,
            )
            async with AsyncSessionFactory() as session:
                stmt = select(ReactionDB).where(
                    ReactionDB.message_id == best_message_id
                )
                result = await session.execute(stmt)
                db_reaction = result.scalar_one_or_none()
                if db_reaction:
                    await session.delete(db_reaction)
                    await session.commit()
                    logger.info(
                        "Deleted reaction log for message %s from DB.",
                        best_message_id,
                    )
        else:
            logger.exception(
                "Failed to pin message %s: %s",
                best_message_id,
                e,
            )
