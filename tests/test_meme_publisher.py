from datetime import date
from unittest import mock

import pytest
from aiogram.types import BufferedInputFile

from app.bot import meme_publisher as mp
from app.bot.meme_generator import MemoryFile

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_bot():
    bot = mock.AsyncMock()
    return bot


@pytest.fixture
def mock_gateway():
    gateway = mock.AsyncMock()
    return gateway


@pytest.fixture
def mock_generate_meme():
    mock_fn = mock.Mock()
    return mock_fn


async def test_success(mock_bot, mock_gateway, mock_generate_meme,
                       monkeypatch):
    """Test successful meme generation and publication."""
    # Setup test data
    test_date = date(2025, 1, 1)
    test_message_id = "123456"
    test_message_text = "This is a test message"

    # Mock buffer returned by generate_meme
    mock_buffer = mock.MagicMock(spec=MemoryFile)
    mock_buffer.getvalue.return_value = b"fake image data"
    mock_generate_meme.return_value = mock_buffer

    # Setup mocks
    mock_gateway.get_best_message_id.return_value = test_message_id
    mock_gateway.get_message_text.return_value = test_message_text
    monkeypatch.setattr(mp, "gateway", mock_gateway)
    monkeypatch.setattr(mp, "generate_meme", mock_generate_meme)

    # Run function
    await mp.generate_and_publish_meme(mock_bot, test_date)

    # Verify gateway interactions
    mock_gateway.get_best_message_id.assert_awaited_once_with(test_date)
    mock_gateway.get_message_text.assert_awaited_once_with(test_message_id)

    # Verify meme was generated
    mock_generate_meme.assert_called_once_with(
        test_message_text,
        mp.UNSPLASH_ACCESS_KEY,
        output_filename="generated_meme.jpg",
    )

    # Verify bot sent photo
    mock_bot.send_photo.assert_awaited_once()
    call_args = mock_bot.send_photo.call_args[1]
    assert call_args["chat_id"] == mp.settings.INNOSCREAM_CHANNEL_ID
    assert isinstance(call_args["photo"], BufferedInputFile)
    assert call_args["caption"] == "Meme generated from most-voted today post"
    assert call_args["disable_notification"] is True


async def test_no_best_message(mock_bot, mock_gateway, monkeypatch):
    """Test when no best message is found."""
    test_date = date(2025, 1, 1)
    mock_gateway.get_best_message_id.return_value = None
    monkeypatch.setattr(mp, "gateway", mock_gateway)

    await mp.generate_and_publish_meme(mock_bot, test_date)

    # Verify gateway interactions
    mock_gateway.get_best_message_id.assert_awaited_once_with(test_date)
    mock_gateway.get_message_text.assert_not_awaited()

    # Verify no message was sent
    mock_bot.send_photo.assert_not_awaited()


async def test_no_message_text(mock_bot, mock_gateway, monkeypatch):
    """Test when no message text is found."""
    test_date = date(2025, 1, 1)
    test_message_id = "123456"

    # Setup mocks
    mock_gateway.get_best_message_id.return_value = test_message_id
    mock_gateway.get_message_text.return_value = None
    monkeypatch.setattr(mp, "gateway", mock_gateway)

    await mp.generate_and_publish_meme(mock_bot, test_date)

    # Verify gateway interactions
    mock_gateway.get_best_message_id.assert_awaited_once_with(test_date)
    mock_gateway.get_message_text.assert_awaited_once_with(test_message_id)

    # Verify no message was sent
    mock_bot.send_photo.assert_not_awaited()


async def test_generation_failed(mock_bot, mock_gateway, mock_generate_meme,
                                 monkeypatch):
    """Test when meme generation fails."""
    test_date = date(2025, 1, 1)
    test_message_id = "123456"
    test_message_text = "This is a test message"

    # Setup mocks
    mock_gateway.get_best_message_id.return_value = test_message_id
    mock_gateway.get_message_text.return_value = test_message_text
    mock_generate_meme.return_value = None
    monkeypatch.setattr(mp, "gateway", mock_gateway)
    monkeypatch.setattr(mp, "generate_meme", mock_generate_meme)

    await mp.generate_and_publish_meme(mock_bot, test_date)

    # Verify gateway interactions
    mock_gateway.get_best_message_id.assert_awaited_once_with(test_date)
    mock_gateway.get_message_text.assert_awaited_once_with(test_message_id)

    # Verify meme generation was attempted
    mock_generate_meme.assert_called_once_with(
        test_message_text,
        mp.UNSPLASH_ACCESS_KEY,
        output_filename="generated_meme.jpg",
    )

    # Verify no message was sent
    mock_bot.send_photo.assert_not_awaited()


async def test_exception(mock_bot, mock_gateway, monkeypatch):
    """Test when an exception occurs."""
    test_date = date(2025, 1, 1)

    # Setup mocks to raise exception
    mock_gateway.get_best_message_id.side_effect = Exception("Test exception")
    monkeypatch.setattr(mp, "gateway", mock_gateway)

    # Should not raise exception
    await mp.generate_and_publish_meme(mock_bot, test_date)

    # Verify gateway interaction was attempted
    mock_gateway.get_best_message_id.assert_awaited_once_with(test_date)

    # Verify no message was sent
    mock_bot.send_photo.assert_not_awaited()
