from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Reaction(BaseModel):
    type: str
    total_count: int


class ReactionUpdate(BaseModel):
    message_id: int
    changed_at: datetime
    reactions: list[Reaction]


class ReactionResponse(BaseModel):
    message_id: int
    changed_at: datetime
    reactions: list[Reaction]

    model_config = ConfigDict(from_attributes=True)
