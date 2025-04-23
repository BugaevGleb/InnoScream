import logging

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.messages import (
    ERROR_MESSAGE,
    INVALID_TEXT,
    START_MESSAGE,
    SUCCESS_MESSAGE,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = Router(name="scream_handler")


@router.message(Command("start"))
async def handle_start_command(message: Message):
    """Handles the /start command.

    Args:
        message: The message object containing the command.
    """
    await message.reply(START_MESSAGE)


@router.message(Command("scream"))
async def handle_scream_command(message: Message, bot: Bot):
    """Handles the /scream command.

    Extracts text and sends it to the target channel.

    Args:
        message: The message object containing the command.
        bot: The bot object.
    """
    if not message.text:
        await message.reply(INVALID_TEXT)
        return

    command_parts = message.text.split(maxsplit=1)
    scream_text = command_parts[1].strip() if len(command_parts) > 1 else ""

    if not scream_text:
        await message.reply(INVALID_TEXT)
        return

    try:
        await bot.send_message(
            chat_id=settings.INNOSCREAM_CHANNEL_ID,
            text=scream_text,
            disable_web_page_preview=True,
        )
        await message.reply(SUCCESS_MESSAGE)
        logger.info(
            "Successfully sent scream to channel %s",
            settings.INNOSCREAM_CHANNEL_ID,
        )
    except Exception as e:
        logger.exception(
            "An error occurred while processing /scream command: %s",
            e,
        )
        await message.reply(ERROR_MESSAGE)
