import pytest
from pydantic import ValidationError

from app.api.schemas import AllStatsResponse, DailyCount, WeeklyStatsResponse


def test_daily_count_valid_data():
    """Test DailyCount schema with valid data."""
    data = DailyCount(day="Mon", count=10)
    assert data.day == "Mon"
    assert data.count == 10


def test_daily_count_invalid_day_type():
    """Test DailyCount with invalid day type."""
    with pytest.raises(ValidationError):
        DailyCount(day=123, count=5)


def test_daily_count_invalid_count_type():
    """Test DailyCount with invalid count type."""
    with pytest.raises(ValidationError):
        DailyCount(day="Tue", count="five")


def test_weekly_stats_valid_structure():
    """Test WeeklyStatsResponse with valid data structure."""
    stats = [DailyCount(day="Wed", count=15)]
    response = WeeklyStatsResponse(stats=stats)
    assert len(response.stats) == 1
    assert response.stats[0].day == "Wed"


def test_weekly_stats_invalid_content_type():
    """Test WeeklyStatsResponse with invalid content type."""
    with pytest.raises(ValidationError):
        WeeklyStatsResponse(stats="invalid")


def test_weekly_stats_invalid_item_type():
    """Test WeeklyStatsResponse with invalid list items."""
    with pytest.raises(ValidationError):
        WeeklyStatsResponse(stats=[{"day": "Thu", "count": "twenty"}])


def test_all_stats_valid_structure():
    """Test AllStatsResponse with valid data structure."""
    stats = [DailyCount(day="Fri", count=20)]
    response = AllStatsResponse(stats=stats)
    assert len(response.stats) == 1
    assert response.stats[0].count == 20


def test_all_stats_empty_list():
    """Test AllStatsResponse with empty stats list."""
    response = AllStatsResponse(stats=[])
    assert len(response.stats) == 0


def test_all_stats_invalid_nested_type():
    """Test AllStatsResponse with invalid nested data."""
    with pytest.raises(ValidationError):
        AllStatsResponse(stats=[{"day": 123, "count": "invalid"}])
