import pytest
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from app.bot.gateways import APIGateway
from app.core.schemas import ReactionUpdate, UserMessage
from httpx import Request, Response, HTTPStatusError

pytestmark = pytest.mark.asyncio


async def test_create_user_message_success():
    """Test create_user_message handles successful request."""
    mock_client = AsyncMock()
    mock_response = MagicMock(spec=Response)
    mock_response.raise_for_status = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    gateway = APIGateway("http://test")
    gateway.client = mock_client
    test_message = UserMessage(
        user_id="123",
        message="test",
        message_id=456,
        created_at=datetime.now(timezone.utc)
    )

    await gateway.create_user_message(test_message)

    mock_client.post.assert_awaited_once_with(
        url="/user_messages",
        json=test_message.model_dump(mode="json")
    )
    mock_response.raise_for_status.assert_called_once()


async def test_create_user_message_error(caplog):
    """Test create_user_message logs exceptions properly."""
    mock_client = AsyncMock()
    mock_client.post.side_effect = Exception("test error")
    gateway = APIGateway("http://test")
    gateway.client = mock_client
    test_message = UserMessage(
        user_id="123",
        message="test",
        message_id=456,
        created_at=datetime.now(timezone.utc)
    )

    await gateway.create_user_message(test_message)
    assert "Error occurred while creating user message" in caplog.text


async def test_delete_user_message_success():
    """Test delete_user_message makes correct API call."""
    mock_client = AsyncMock()
    mock_response = MagicMock(spec=Response)
    mock_response.raise_for_status = MagicMock()
    mock_client.delete = AsyncMock(return_value=mock_response)

    gateway = APIGateway("http://test")
    gateway.client = mock_client

    await gateway.delete_user_message(123)

    mock_client.delete.assert_awaited_once_with(url="/user_messages/123")
    mock_response.raise_for_status.assert_called_once()


async def test_delete_user_message_error(caplog):
    """Test delete_user_message logs exceptions properly."""
    mock_client = AsyncMock()
    mock_client.delete.side_effect = Exception("test error")
    gateway = APIGateway("http://test")
    gateway.client = mock_client

    await gateway.delete_user_message(123)
    assert "Error occurred while deleting user message" in caplog.text


async def test_get_best_message_id_success():
    """Test get_best_message_id returns valid ID."""
    mock_client = AsyncMock()
    mock_response = MagicMock(spec=Response)
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value=123)
    mock_client.get = AsyncMock(return_value=mock_response)

    gateway = APIGateway("http://test")
    gateway.client = mock_client
    test_date = date.today()

    result = await gateway.get_best_message_id(test_date)

    assert result == 123
    mock_client.get.assert_awaited_once_with(
        url="/user_messages/best", params={"today": test_date.isoformat()}
    )
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


async def test_get_best_message_id_http_error(caplog):
    """Test get_best_message_id handles HTTP errors."""
    mock_client = AsyncMock()
    mock_request = MagicMock(spec=Request)
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 500
    http_error = HTTPStatusError(
        "Server Error", request=mock_request, response=mock_response
    )
    mock_client.get.side_effect = http_error

    gateway = APIGateway("http://test")
    gateway.client = mock_client
    test_date = date.today()

    result = await gateway.get_best_message_id(test_date)

    assert result is None
    mock_client.get.assert_awaited_once_with(
        url="/user_messages/best", params={"today": test_date.isoformat()}
    )
    assert "HTTP error occurred while getting best message" in caplog.text


async def test_get_message_text_success():
    """Test get_message_text returns valid text."""
    mock_client = AsyncMock()
    mock_response = MagicMock(spec=Response)
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"message": "Test Text"})
    mock_client.get = AsyncMock(return_value=mock_response)

    gateway = APIGateway("http://test")
    gateway.client = mock_client

    result = await gateway.get_message_text(123)

    assert result == "Test Text"
    mock_client.get.assert_awaited_once_with(url="/user_messages/123")
    mock_response.raise_for_status.assert_called_once()
    mock_response.json.assert_called_once()


async def test_get_message_text_error(caplog):
    """Test get_message_text returns None on error."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("test error")
    gateway = APIGateway("http://test")
    gateway.client = mock_client

    result = await gateway.get_message_text(123)

    assert result is None
    mock_client.get.assert_awaited_once_with(url="/user_messages/123")
    assert "Error occurred while getting message text" in caplog.text


async def test_update_reaction_success():
    """Test update_reaction handles successful request."""
    mock_client = AsyncMock()
    mock_response = MagicMock(spec=Response)
    mock_response.raise_for_status = MagicMock()
    mock_client.put = AsyncMock(return_value=mock_response)

    gateway = APIGateway("http://test")
    gateway.client = mock_client
    test_update = ReactionUpdate(
        message_id=789,
        changed_at=datetime.now(timezone.utc),
        reactions=[]
    )

    await gateway.update_reaction(test_update)

    mock_client.put.assert_awaited_once_with(
        url="/reactions",
        json=test_update.model_dump(mode="json")
    )
    mock_response.raise_for_status.assert_called_once()


async def test_update_reaction_error(caplog):
    """Test update_reaction logs exceptions properly."""
    mock_client = AsyncMock()
    mock_client.put.side_effect = Exception("test error")
    gateway = APIGateway("http://test")
    gateway.client = mock_client
    test_update = ReactionUpdate(
        message_id=789,
        changed_at=datetime.now(timezone.utc),
        reactions=[]
    )

    await gateway.update_reaction(test_update)
    assert "Error occurred while updating reaction" in caplog.text
