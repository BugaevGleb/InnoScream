import logging
from datetime import date

import httpx
from aiogram import Bot
from aiogram.types import BufferedInputFile
from app.core.config import settings

from app.bot.meme_generator import generate_meme
from app.bot.pin_most_voted import get_best_message_id

logger = logging.getLogger(__name__)


API_URL = settings.INNOSCREAM_API_URL
UNSPLASH_ACCESS_KEY = settings.UNSPLASH_ACCESS_KEY


async def get_message_text(message_id: int) -> str:
    """Retrieves the user message text by its message_id."""
    async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
        response = await client.get(f"{API_URL}/user_messages/{message_id}")
        response.raise_for_status()
        message_data = response.json()
        text = message_data.get("message", "")
        logger.info(
            "Message text for id %s retrieved: %s",
            message_id, text)
        return text


async def generate_and_publish_meme(bot: Bot, today: date | None = None):
    """Generates and publishes memes from best posts."""
    try:
        best_message_id = await get_best_message_id(today)
        if best_message_id is None:
            logger.info("No best message id found for today %s.", today)
            return

        message_text = await get_message_text(best_message_id)
        if not message_text:
            logger.warning(
                "No message text found for message id %s.",
                best_message_id)
            return

        meme_buffer = generate_meme(
            message_text,
            UNSPLASH_ACCESS_KEY,
            output_filename="generated_meme.jpg")
        if meme_buffer is None:
            logger.error(
                "Meme generation failed for message id %s.",
                best_message_id)
            return

        logger.info("Meme generated in memory, now sending to channel.")
        meme_bytes = meme_buffer.getvalue()
        input_file = BufferedInputFile(meme_bytes, filename="meme.jpg")

        await bot.send_photo(
            chat_id=settings.INNOSCREAM_CHANNEL_ID,
            photo=input_file,
            caption="Meme generated from most-voted today post",
            disable_notification=True,
        )
        logger.info(
            "Meme published successfully for message id %s.",
            best_message_id)
    except Exception as e:
        logger.exception("Error in generate_and_publish_meme: %s", e)
