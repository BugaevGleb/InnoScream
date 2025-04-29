from pydantic import BaseModel


class DailyCount(BaseModel):
    day: str  # e.g., 'Mon', 'Tue' etc.
    count: int


class WeeklyStatsResponse(BaseModel):
    stats: list[DailyCount]


class AllStatsResponse(BaseModel):
    stats: list[DailyCount]
