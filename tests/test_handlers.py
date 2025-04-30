import hashlib
import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import (
    Chat,
    Message,
    User,
)

from app.bot.handlers import (
    ADMIN_START_MESSAGE,
    ERROR_MESSAGE,
    INVALID_TEXT,
    MEME_MESSAGE,
    PIN_MESSAGE,
    START_MESSAGE,
    handle_delete_command,
    handle_generate_meme_command,
    handle_pin_command,
    handle_scream_command,
    handle_start_command,
    handle_stats_command,
)

TEST_USER_ID = 12345
TEST_ADMIN_ID = 67890
TEST_CHAT_ID = -1001234567890
TEST_MESSAGE_ID = 555
TEST_REPLY_MESSAGE_ID = 554
TEST_CHANNEL_ID = TEST_CHAT_ID
TEST_API_URL = "http://test.com"
TEST_TIMEOUT = 5
TEST_TEXT = "This is a test scream!"
TEST_HASHED_USER_ID = hashlib.sha256(str(TEST_USER_ID).encode()).hexdigest()
TEST_NOW = datetime.now(timezone.utc)


@pytest.fixture
def mock_bot():
    """Provides a mock Bot instance."""
    bot = AsyncMock()
    bot.send_message = AsyncMock(
        return_value=Message(
            message_id=TEST_MESSAGE_ID,
            chat=Chat(id=TEST_CHANNEL_ID, type="channel"),
            date=TEST_NOW)
    )
    bot.delete_message = AsyncMock()
    return bot


@pytest.fixture
def mock_message():
    """Provides a mock Message instance."""
    message = AsyncMock(spec=Message)
    message.message_id = TEST_MESSAGE_ID
    message.from_user = User(id=TEST_USER_ID, is_bot=False, first_name="Test")
    message.chat = Chat(id=TEST_USER_ID, type="private")
    message.date = TEST_NOW
    message.text = ""
    message.reply = AsyncMock()
    message.reply_to_message = None
    return message


@pytest.fixture
def mock_admin_message(mock_message):
    """Provides a mock Message instance from an admin."""
    mock_message.from_user = User(
        id=TEST_ADMIN_ID, is_bot=False, first_name="Admin"
    )
    return mock_message


@pytest.fixture
def mock_channel_post(mock_message):
    """Provides a mock Message instance representing a channel post."""
    mock_message.chat = Chat(id=TEST_CHANNEL_ID, type="channel")
    mock_message.sender_chat = Chat(id=TEST_CHANNEL_ID, type="channel")
    mock_message.from_user = None
    mock_message.is_automatic_forward = None
    return mock_message


@pytest.fixture
def mock_settings(mocker):
    """Provides mock settings."""
    mock_settings_obj = MagicMock()
    mock_settings_obj.ADMIN_IDS = [TEST_ADMIN_ID]
    mock_settings_obj.INNOSCREAM_CHANNEL_ID = TEST_CHANNEL_ID
    mock_settings_obj.INNOSCREAM_API_URL = TEST_API_URL
    mock_settings_obj.HTTP_TIMEOUT = TEST_TIMEOUT
    mocker.patch("app.bot.handlers.settings", mock_settings_obj)
    mocker.patch("app.bot.pin_most_voted.settings", mock_settings_obj)
    mocker.patch("app.bot.meme_publisher.settings", mock_settings_obj)
    return mock_settings_obj


@pytest.fixture
def mock_gateway(mocker):
    """Provides a mock APIGateway instance."""
    mock_gw = AsyncMock()
    mock_gw.create_user_message = AsyncMock()
    mock_gw.get_user_stats = AsyncMock(return_value=5)
    mock_gw.update_reaction = AsyncMock()
    mock_gw.delete_user_message = AsyncMock()
    mocker.patch("app.bot.handlers.APIGateway", return_value=mock_gw)
    return mock_gw


@pytest.fixture
def mock_pin_best_message(mocker):
    """Mocks the pin_best_message function."""
    return mocker.patch(
        "app.bot.handlers.pin_best_message", new_callable=AsyncMock
    )


@pytest.fixture
def mock_generate_meme(mocker):
    """Mocks the generate_and_publish_meme function."""
    return mocker.patch(
        "app.bot.handlers.generate_and_publish_meme", new_callable=AsyncMock
    )


@pytest.mark.asyncio
async def test_handle_start_command_admin(
    mock_admin_message, mock_settings
):
    """Test /start command from an admin user."""
    await handle_start_command(mock_admin_message)
    mock_admin_message.reply.assert_called_once_with(ADMIN_START_MESSAGE)


@pytest.mark.asyncio
async def test_handle_start_command_user(mock_message, mock_settings):
    """Test /start command from a regular user."""
    await handle_start_command(mock_message)
    mock_message.reply.assert_called_once_with(START_MESSAGE)


@pytest.mark.asyncio
async def test_handle_pin_command_admin(
    mock_admin_message, mock_bot, mock_settings, mock_pin_best_message
):
    """Test /pin command from an admin user."""
    await handle_pin_command(mock_admin_message, mock_bot)
    mock_admin_message.reply.assert_called_once_with(PIN_MESSAGE)
    mock_pin_best_message.assert_called_once_with(mock_bot)


@pytest.mark.asyncio
async def test_handle_pin_command_user(
    mock_message, mock_bot, mock_settings, mock_pin_best_message
):
    """Test /pin command from a regular user (should do nothing)."""
    await handle_pin_command(mock_message, mock_bot)
    mock_message.reply.assert_not_called()
    mock_pin_best_message.assert_not_called()


@pytest.mark.asyncio
async def test_handle_pin_command_no_user(
    mock_message, mock_bot, mock_settings, mock_pin_best_message
):
    """Test /pin command when from_user is None."""
    mock_message.from_user = None
    await handle_pin_command(mock_message, mock_bot)
    mock_message.reply.assert_not_called()
    mock_pin_best_message.assert_not_called()


@pytest.mark.asyncio
async def test_handle_generate_meme_command_admin(
    mock_admin_message, mock_bot, mock_settings, mock_generate_meme
):
    """Test /generate_meme command from an admin user."""
    await handle_generate_meme_command(mock_admin_message, mock_bot)
    mock_admin_message.reply.assert_called_once_with(MEME_MESSAGE)
    mock_generate_meme.assert_called_once_with(mock_bot)


@pytest.mark.asyncio
async def test_handle_generate_meme_command_user(
    mock_message, mock_bot, mock_settings, mock_generate_meme
):
    """Test /generate_meme command from a regular user (should do nothing)."""
    await handle_generate_meme_command(mock_message, mock_bot)
    mock_message.reply.assert_not_called()
    mock_generate_meme.assert_not_called()


@pytest.mark.asyncio
async def test_handle_generate_meme_command_no_user(
    mock_message, mock_bot, mock_settings, mock_generate_meme
):
    """Test /generate_meme command when from_user is None."""
    mock_message.from_user = None
    await handle_generate_meme_command(mock_message, mock_bot)
    mock_message.reply.assert_not_called()
    mock_generate_meme.assert_not_called()


@pytest.mark.asyncio
async def test_handle_scream_command_no_user(
    mock_message, mock_bot, mock_gateway, mock_settings
):
    """Test /scream command when from_user is None."""
    mock_message.from_user = None
    mock_message.text = f"/scream {TEST_TEXT}"
    await handle_scream_command(mock_message, mock_bot)
    mock_message.reply.assert_called_once_with(ERROR_MESSAGE)
    mock_bot.send_message.assert_not_called()
    mock_gateway.create_user_message.assert_not_called()


@pytest.mark.asyncio
async def test_handle_scream_command_no_message_text(
    mock_message, mock_bot, mock_gateway, mock_settings
):
    """Test /scream command when message.text is None."""
    mock_message.text = None
    await handle_scream_command(mock_message, mock_bot)
    mock_message.reply.assert_called_once_with(INVALID_TEXT)
    mock_bot.send_message.assert_not_called()
    mock_gateway.create_user_message.assert_not_called()


@pytest.mark.asyncio
async def test_handle_scream_command_no_scream_text(
    mock_message, mock_bot, mock_gateway, mock_settings
):
    """Test /scream command with no text after the command."""
    mock_message.text = "/scream"
    await handle_scream_command(mock_message, mock_bot)
    mock_message.reply.assert_called_once_with(INVALID_TEXT)
    mock_bot.send_message.assert_not_called()
    mock_gateway.create_user_message.assert_not_called()


@pytest.mark.asyncio
async def test_handle_scream_command_only_whitespace_text(
    mock_message, mock_bot, mock_gateway, mock_settings
):
    """Test /scream command with only whitespace after the command."""
    mock_message.text = "/scream  \t "
    await handle_scream_command(mock_message, mock_bot)
    mock_message.reply.assert_called_once_with(INVALID_TEXT)
    mock_bot.send_message.assert_not_called()
    mock_gateway.create_user_message.assert_not_called()


@pytest.mark.asyncio
async def test_handle_scream_command_send_exception(
    mock_message, mock_bot, mock_gateway, mock_settings, caplog
):
    """Test /scream command when bot.send_message fails."""
    mock_message.text = f"/scream {TEST_TEXT}"
    mock_bot.send_message.side_effect = Exception("Send failed")
    caplog.set_level(logging.ERROR)

    await handle_scream_command(mock_message, mock_bot)

    mock_message.reply.assert_called_once_with(ERROR_MESSAGE)
    mock_gateway.create_user_message.assert_not_called()
    assert "An error occurred while processing /scream command" in caplog.text
    assert "Send failed" in caplog.text


@pytest.mark.asyncio
async def test_handle_stats_command_no_user(
    mock_message, mock_gateway, mock_settings, caplog
):
    """Test /stats command when from_user is None."""
    mock_message.from_user = None
    caplog.set_level(logging.ERROR)
    await handle_stats_command(mock_message)
    mock_message.reply.assert_called_once_with(ERROR_MESSAGE)
    mock_gateway.get_user_stats.assert_not_called()
    assert "Cannot get stats: message.from_user is None." in caplog.text


@pytest.mark.asyncio
async def test_handle_delete_command_no_reply(
    mock_channel_post, mock_bot, mock_gateway, mock_settings
):
    """Test /delete command without replying to a message."""
    mock_channel_post.text = "/delete"
    mock_channel_post.reply_to_message = None

    await handle_delete_command(mock_channel_post, mock_bot)

    mock_channel_post.reply.assert_called_once_with(
        "Please reply to a message you want to delete."
    )
    mock_bot.delete_message.assert_not_called()
    mock_gateway.delete_user_message.assert_not_called()


@pytest.mark.asyncio
async def test_handle_delete_command_delete_exception(
    mock_channel_post, mock_bot, mock_gateway, mock_settings, caplog
):
    """Test /delete command when bot.delete_message fails."""
    mock_channel_post.text = "/delete"
    mock_channel_post.reply_to_message = Message(
        message_id=TEST_REPLY_MESSAGE_ID,
        chat=mock_channel_post.chat,
        date=TEST_NOW,
    )
    mock_bot.delete_message.side_effect = Exception("Delete failed")
    caplog.set_level(logging.ERROR)

    await handle_delete_command(mock_channel_post, mock_bot)

    mock_bot.delete_message.assert_called_once_with(
        chat_id=TEST_CHANNEL_ID, message_id=TEST_REPLY_MESSAGE_ID
    )
    mock_gateway.delete_user_message.assert_not_called()
    mock_channel_post.reply.assert_not_called()
    assert "An error occurred while deleting message" in caplog.text
    assert "Delete failed" in caplog.text
