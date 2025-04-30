import pytest
from aiogram.exceptions import TelegramBadRequest
from app.bot import pin_most_voted as p
from unittest.mock import AsyncMock


class DummyGateway:
    """Dummy gateway for tests."""
    async def get_best_message_id(self, today):
        return self.best_id

    async def delete_user_message(self, best_message_id):
        self.deleted = best_message_id


@pytest.fixture
def dummy_gateway(monkeypatch):
    """Provide a dummy gateway and patch the module."""
    dummy = DummyGateway()
    dummy.best_id = 123
    dummy.deleted = None
    monkeypatch.setattr(p, "gateway", dummy)
    return dummy


@pytest.fixture
def dummy_bot():
    """Return a dummy bot."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_pin_best_message_success(dummy_bot, dummy_gateway):
    """Test pin_best_message success branch."""
    async def return_id(today):
        return 123
    dummy_gateway.best_id = 123
    dummy_gateway.get_best_message_id = return_id
    dummy_bot.pin_chat_message = AsyncMock()
    await p.pin_best_message(dummy_bot, today="2021-01-01")
    dummy_bot.pin_chat_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_pin_best_message_no_message(dummy_bot, dummy_gateway,
                                           monkeypatch):
    """Test branch when no best message id."""
    async def return_none(today):
        return None
    monkeypatch.setattr(dummy_gateway, "get_best_message_id",
                        return_none)
    await p.pin_best_message(dummy_bot, today="2021-01-01")
    dummy_bot.pin_chat_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_pin_best_message_other_error(
        dummy_bot, dummy_gateway, monkeypatch):
    """Test branch for non-invalid error."""
    async def return_789(today):
        return 789
    monkeypatch.setattr(dummy_gateway, "get_best_message_id",
                        return_789)

    async def fake_pin(*args, **kwargs):
        raise TelegramBadRequest("Other error", "dummy")
    dummy_bot.pin_chat_message = AsyncMock(side_effect=fake_pin)
    dummy_gateway.deleted = None
    await p.pin_best_message(dummy_bot, today="2021-01-01")
    assert dummy_gateway.deleted is None
