from datetime import datetime

from ninja import Schema

from hubflow.accounts.schemas import UserOut


class TimeEntryOut(Schema):
    id: int
    card_id: int
    user: UserOut
    started_at: datetime
    ended_at: datetime | None
    note: str
    is_manual: bool
    is_running: bool
    hours: float


class CardTimeOut(Schema):
    entries: list[TimeEntryOut]
    total_hours: float
    running: TimeEntryOut | None
