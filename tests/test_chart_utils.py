import json
import urllib.parse
import pytest
import httpx
from unittest.mock import AsyncMock
from app.bot import chart_utils as wc


@pytest.fixture
def dummy_stats():
    """Return dummy stats."""
    return [
        {"day": "Mon", "count": 10},
        {"day": "Tue", "count": 5},
        {"day": "Wed", "count": 7},
        {"day": "Thu", "count": 3},
        {"day": "Fri", "count": 8},
        {"day": "Sat", "count": 2},
        {"day": "Sun", "count": 0},
    ]


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    """Patch settings for tests."""
    class FakeSettings:
        HTTP_TIMEOUT = 5
        INNOSCREAM_API_URL = "http://fake.api"
        INNOSCREAM_CHANNEL_ID = 12345
        ADMIN_IDS = [99999]
    monkeypatch.setattr(wc, "settings", FakeSettings())


def test_generate_weekly_chart_url_full(dummy_stats):
    """Test URL generation from full stats."""
    url = wc.generate_weekly_stress_chart_url(dummy_stats)
    assert url.startswith(wc.BASE_URL + "?c=")
    cfg_str = urllib.parse.unquote(url.split("?c=")[-1])
    cfg = json.loads(cfg_str)
    assert cfg.get("type") == "bar"
    data = cfg.get("data", {}).get("datasets", [{}])[0].get("data", [])
    expected = [10, 5, 7, 3, 8, 2, 0]
    assert data == expected


def test_generate_weekly_chart_url_missing():
    """Test URL generation with missing days."""
    dummy = [
        {"day": "Mon", "count": 12},
        {"day": "Wed", "count": 3},
        {"day": "Fri", "count": 2},
    ]
    url = wc.generate_weekly_stress_chart_url(dummy)
    cfg_str = urllib.parse.unquote(url.split("?c=")[-1])
    cfg = json.loads(cfg_str)
    data = cfg.get("data", {}).get("datasets", [{}])[0].get("data", [])
    expected = [12, 0, 3, 0, 2, 0, 0]
    assert data == expected


class DummyResponse:
    """Dummy response for async get."""

    def __init__(self, json_data, status_code=200, content=b""):
        self._json = json_data
        self.status_code = status_code
        self._content = content

    def json(self):
        """Return JSON data."""
        return self._json

    def raise_for_status(self):
        """Raise error if status is not 200."""
        if self.status_code != 200:
            raise httpx.HTTPStatusError("err", request=None,
                                        response=self)

    @property
    def content(self):
        """Return content bytes."""
        return self._content


class DummyAsyncClient:
    """Dummy async client for HTTPX."""

    def __init__(self, response):
        self._response = response

    async def get(self, *args, **kwargs):
        """Async get returns dummy response."""
        return self._response

    async def __aenter__(self):
        """Enter context."""
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit context."""
        pass


@pytest.fixture
def dummy_bot():
    """Return a dummy bot with async send_message."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_send_weekly_chart_success(
        monkeypatch, dummy_stats, dummy_bot):
    """Test send_weekly_chart success branch."""
    response = DummyResponse({"stats": dummy_stats})
    monkeypatch.setattr(httpx, "AsyncClient",
                        lambda timeout: DummyAsyncClient(response))
    monkeypatch.setattr(wc, "generate_weekly_stress_chart_url",
                        lambda stats: "http://chart.url")
    await wc.send_weekly_chart(dummy_bot)
    dummy_bot.send_message.assert_awaited_once()
    args, kwargs = dummy_bot.send_message.call_args
    text = args[1] if args and len(args) > 1 else kwargs.get("text", "")
    assert "http://chart.url" in text


@pytest.mark.asyncio
async def test_send_weekly_chart_no_stats(monkeypatch, dummy_bot):
    """Test send_weekly_chart with no stats data."""
    response = DummyResponse({})
    monkeypatch.setattr(httpx, "AsyncClient",
                        lambda timeout: DummyAsyncClient(response))
    await wc.send_weekly_chart(dummy_bot)
    dummy_bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_weekly_chart_no_channel(
        monkeypatch, dummy_stats, dummy_bot):
    """Test send_weekly_chart with no channel set."""
    # Override settings so no channel is configured.
    class FakeNoChannel:
        HTTP_TIMEOUT = 5
        INNOSCREAM_API_URL = "http://fake.api"
        INNOSCREAM_CHANNEL_ID = None
        ADMIN_IDS = []  # Admin IDs empty so no error msg.
    monkeypatch.setattr(wc, "settings", FakeNoChannel())
    response = DummyResponse({"stats": dummy_stats})
    monkeypatch.setattr(httpx, "AsyncClient",
                        lambda timeout: DummyAsyncClient(response))
    monkeypatch.setattr(wc, "generate_weekly_stress_chart_url",
                        lambda stats: "http://chart.url")
    await wc.send_weekly_chart(dummy_bot)
    dummy_bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_weekly_chart_http_error(monkeypatch, dummy_bot):
    """Test send_weekly_chart HTTP error branch."""
    class ClientError:
        async def get(self, *args, **kwargs):
            raise httpx.HTTPStatusError(
                "err", request=None,
                response=DummyResponse({}, 400))

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass
    monkeypatch.setattr(httpx, "AsyncClient",
                        lambda timeout: ClientError())
    await wc.send_weekly_chart(dummy_bot)
    dummy_bot.send_message.assert_awaited_once()
    args, kwargs = dummy_bot.send_message.call_args
    text = args[1] if args and len(args) > 1 else kwargs.get("text", "")
    assert "Error generating weekly stress chart" in text


@pytest.mark.asyncio
async def test_send_weekly_chart_generic_exception(
        monkeypatch, dummy_bot):
    """Test send_weekly_chart generic exception branch."""
    class ClientException:
        async def get(self, *args, **kwargs):
            raise Exception("gen error")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass
    monkeypatch.setattr(httpx, "AsyncClient",
                        lambda timeout: ClientException())
    await wc.send_weekly_chart(dummy_bot)
    dummy_bot.send_message.assert_awaited_once()
    args, kwargs = dummy_bot.send_message.call_args
    text = args[1] if args and len(args) > 1 else kwargs.get("text", "")
    assert "Error generating weekly stress chart" in text


def test_load_chart_config():
    labels = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    data = [5, 10, 7, 9, 6]

    config = wc.load_chart_config("app/cfg/chart_config.json", labels, data)

    assert config['data']['labels'] == labels
    assert config['data']['datasets'][0]['data'] == data

    assert config['type'] == 'bar'
    assert config['options']['title']['text'] == 'Weekly Stress '\
        'Levels (Screams per Day)'


def test_get_days_order():
    """Test that get_days_order returns the expected list of days."""
    days = wc.get_days_order()
    expected_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    assert days == expected_days
