import pytest
from unittest.mock import AsyncMock, MagicMock

from app.bot import meme_publisher as mp

pytestmark = pytest.mark.asyncio


async def test_generate_and_publish_meme_success(mocker):
    """Test generate_and_publish_meme sends photo on success."""
    bot = AsyncMock()
    mocker.patch.object(mp.gateway, "get_best_message_id", return_value=123)
    mocker.patch.object(
        mp.gateway,
        "get_message_text",
        return_value="cat meme")
    dummy_buffer = MagicMock()
    dummy_buffer.getvalue.return_value = b"dummy image bytes"
    mocker.patch(
        "app.bot.meme_publisher.generate_meme",
        return_value=dummy_buffer)
    await mp.generate_and_publish_meme(bot)
    bot.send_photo.assert_awaited_once()


async def test_generate_and_publish_meme_no_best(mocker):
    """Test generate_and_publish_meme skips when no best message."""
    bot = AsyncMock()
    mocker.patch.object(mp.gateway, "get_best_message_id", return_value=None)
    await mp.generate_and_publish_meme(bot)
    bot.send_photo.assert_not_called()


async def test_generate_and_publish_meme_no_text(mocker):
    """Test generate_and_publish_meme skips when message has no text."""
    bot = AsyncMock()
    mocker.patch.object(mp.gateway, "get_best_message_id", return_value=123)
    mocker.patch.object(mp.gateway, "get_message_text", return_value=None)
    await mp.generate_and_publish_meme(bot)
    bot.send_photo.assert_not_called()


async def test_generate_and_publish_meme_gen_fail(mocker):
    """Test generate_and_publish_meme skips when meme generation fails."""
    bot = AsyncMock()
    mocker.patch.object(mp.gateway, "get_best_message_id", return_value=123)
    mocker.patch.object(mp.gateway, "get_message_text", return_value="funny")
    mocker.patch("app.bot.meme_publisher.generate_meme", return_value=None)
    await mp.generate_and_publish_meme(bot)
    bot.send_photo.assert_not_called()


async def test_generate_and_publish_meme_exception(mocker):
    """Test generate_and_publish_meme handles gateway exceptions."""
    bot = AsyncMock()
    mocker.patch.object(
        mp.gateway,
        "get_best_message_id",
        side_effect=RuntimeError("API failure")
    )
    await mp.generate_and_publish_meme(bot)
    bot.send_photo.assert_not_called()
