import logging
from sqlalchemy import select, func
from app.core.models import Reaction as ReactionDB, UserMessage as UserMessageDB
from app.core.database import AsyncSessionFactory
from aiogram import Bot
from app.core.config import settings
from aiogram.exceptions import TelegramBadRequest
from datetime import date

logger = logging.getLogger(__name__)

async def get_best_message_id():
    today = date.today()

    async with AsyncSessionFactory() as session:
        stmt = select(ReactionDB).join(
            UserMessageDB, UserMessageDB.message_id == ReactionDB.message_id
        ).where(
            func.date(UserMessageDB.created_at) == today
        )
        result = await session.execute(stmt)
        reactions = result.scalars().all()

        logger.info(f'Found {len(reactions)} reactions today.')

        if not reactions:
            logger.info('No reactions found for today.')
            return None

        message_reaction_sums = {
            reaction.message_id: sum(r.get('total_count', 0) for r in reaction.reactions)
            for reaction in reactions
        }
        logger.info(f'Message reaction sums: {message_reaction_sums}')

        best_message_id = max(message_reaction_sums, key=message_reaction_sums.get)

        logger.info(f"Best message_id selected: {best_message_id}")
        return best_message_id

async def pin_best_message(bot: Bot):
    best_message_id = await get_best_message_id()
    if not best_message_id:
        logger.info("No messages to pin.")
        return

    try:
        await bot.pin_chat_message(
            chat_id=settings.INNOSCREAM_CHANNEL_ID,
            message_id=best_message_id,
            disable_notification=True
        )
        logger.info(f"Pinned message {best_message_id} successfully.")
    except TelegramBadRequest as e:
        if 'MESSAGE_ID_INVALID' in str(e):
            logger.warning(f"Message {best_message_id} not found or deleted. Removing from DB.")
            async with AsyncSessionFactory() as session:
                stmt = select(ReactionDB).where(ReactionDB.message_id == best_message_id)
                result = await session.execute(stmt)
                db_reaction = result.scalar_one_or_none()
                if db_reaction:
                    await session.delete(db_reaction)
                    await session.commit()
                    logger.info(f"Deleted reaction log for message {best_message_id} from DB.")
        else:
            logger.exception(f"Failed to pin message {best_message_id}: {e}")
