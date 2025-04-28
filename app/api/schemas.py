from pydantic import BaseModel

# TODO: add api schemas here


class DailyCount(BaseModel):
    day: str  # e.g., 'Mon', 'Tue' etc.
    count: int


class WeeklyStatsResponse(BaseModel):
    stats: list[DailyCount]


class AllStatsResponse(BaseModel):
    stats: list[DailyCount]
