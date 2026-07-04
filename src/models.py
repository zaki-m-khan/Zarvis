"""Structured check-in schema (Phase 1)."""
from pydantic import BaseModel


class CheckIn(BaseModel):
    gym: bool | None = None          # lift completed today
    outreach: int | None = None      # personalized outreaches sent today
    calls: int | None = None         # coffee chats / calls booked today
    clay: bool | None = None         # Clay table shipped
    steps: int | None = None         # today's step count
    weight: float | None = None      # morning weigh-in (lbs)
    milestone: bool | None = None    # flagship project milestone hit

    def has_data(self) -> bool:
        return any(v is not None for v in self.model_dump().values())
