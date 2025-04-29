import hashlib
import logging

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message, MessageReactionCountUpdated

from app.bot.gateways import APIGateway
from app.bot.meme_publisher import generate_and_publish_meme
from app.bot.messages import (
    ERROR_MESSAGE,
    INVALID_TEXT,
    MEME_MESSAGE,
    PIN_MESSAGE,
    START_MESSAGE,
    STATS_MESSAGE,
    SUCCESS_MESSAGE,
)
from app.bot.pin_most_voted import pin_best_message
from app.core.config import settings
from app.core.schemas import Reaction, ReactionUpdate, UserMessage

logger = logging.getLogger(__name__)

router = Router(name="scream_handler")
channel_router = Router(name="channel_handler")

gateway = APIGateway(settings.INNOSCREAM_API_URL, settings.HTTP_TIMEOUT)


@router.message(Command("start"))
async def handle_start_command(message: Message):
    """Handles the /start command.

    Args:
        message: The message object containing the command.
    """
    await message.reply(START_MESSAGE)


@router.message(Command("pin"))
async def handle_pin_command(message: Message, bot: Bot):
    """Handles the /pin command.

    Only admins can use this command.

    Args:
        message: The message object containing the command.
        bot: The Bot instance.
    """
    if (
        message.from_user is None
        or message.from_user.id not in settings.ADMIN_IDS
    ):
        return

    await message.reply(PIN_MESSAGE)
    await pin_best_message(bot)


@router.message(Command("generate_meme"))
async def handle_generate_meme_command(message: Message, bot: Bot):
    """Handles the /generate_meme command.

    Only admins can use this command.

    Args:
        message: The message object containing the command.
        bot: The Bot instance.
    """
    if (
        message.from_user is None
        or message.from_user.id not in settings.ADMIN_IDS
    ):
        return

    await message.reply(MEME_MESSAGE)
    await generate_and_publish_meme(bot)


@router.message(Command("scream"))
async def handle_scream_command(message: Message, bot: Bot):
    """Handles the /scream command.

    Extracts text and sends it to the target channel.

    Args:
        message: The message object containing the command.
        bot: The bot object.
    """
    if message.from_user is None:
        await message.reply(ERROR_MESSAGE)
        return

    if not message.text:
        await message.reply(INVALID_TEXT)
        return

    command_parts = message.text.split(maxsplit=1)
    scream_text = command_parts[1].strip() if len(command_parts) > 1 else ""

    if not scream_text:
        await message.reply(INVALID_TEXT)
        return

    try:
        channel_message = await bot.send_message(
            chat_id=settings.INNOSCREAM_CHANNEL_ID,
            text=scream_text,
            disable_web_page_preview=True,
        )
        user_message = UserMessage(
            message_id=channel_message.message_id,
            user_id=hashlib.sha256(
                str(message.from_user.id).encode()
            ).hexdigest(),
            message=scream_text,
            created_at=message.date,
        )
        await gateway.create_user_message(user_message)
        await message.reply(SUCCESS_MESSAGE)
        logger.info(
            "Successfully sent scream message with id %s to channel %s",
            message.message_id,
            settings.INNOSCREAM_CHANNEL_ID,
        )
    except Exception as e:
        logger.exception(
            "An error occurred while processing /scream command: %s",
            e,
        )
        await message.reply(ERROR_MESSAGE)


@router.message(Command("stats"))
async def handle_stats_command(message: Message):
    """Handles the /stats command.

    Retrieves and sends the user's personal message count.

    Args:
        message: The message object containing the command.
    """
    if not message.from_user:
        logger.error("Cannot get stats: message.from_user is None.")
        await message.reply(ERROR_MESSAGE)
        return

    user_id_hashed = hashlib.sha256(
        str(message.from_user.id).encode()
    ).hexdigest()

    count = await gateway.get_user_stats(user_id_hashed)
    await message.reply(STATS_MESSAGE.format(count=count))
    logger.info("Successfully sent stats for user %s", user_id_hashed)


@router.message_reaction_count()
async def handle_reaction_count(message: MessageReactionCountUpdated):
    """Handles the message reaction count.

    Args:
        message: The message object containing the reaction count.
    """
    reaction_update = ReactionUpdate(
        message_id=message.message_id,
        changed_at=message.date,
        reactions=[
            Reaction(
                type=reaction.type.emoji,  # type: ignore
                total_count=reaction.total_count,
            )
            for reaction in message.reactions
        ],
    )
    logger.info("Reaction update: %s", reaction_update)
    await gateway.update_reaction(reaction_update)


@channel_router.channel_post(Command("delete"))
async def handle_delete_command(message: Message, bot: Bot):
    """Handles the /delete command for channel messages.

    Args:
        message: The message object containing the command.
        bot: The bot object.
    """
    if message.chat.id != settings.INNOSCREAM_CHANNEL_ID:
        return False

    if not message.reply_to_message:
        await message.reply("Please reply to a message you want to delete.")
        return

    target_message_id = message.reply_to_message.message_id
    target_chat_id = message.chat.id

    try:
        await bot.delete_message(
            chat_id=target_chat_id, message_id=target_message_id
        )

        await gateway.delete_user_message(target_message_id)

        # Also delete the command message
        await bot.delete_message(
            chat_id=message.chat.id, message_id=message.message_id
        )

        logger.info(
            "Successfully deleted message %s from chat %s",
            target_message_id,
            target_chat_id,
        )
    except Exception as e:
        logger.exception(
            "An error occurred while deleting message: %s",
            e,
        )
