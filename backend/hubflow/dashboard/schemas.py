from datetime import date, datetime

from ninja import Schema

from hubflow.accounts.schemas import UserOut
from hubflow.boards.schemas import CardOut


class ColumnCountOut(Schema):
    key: str
    label: str
    count: int


class DashboardCardOut(CardOut):
    project_name: str
    client_name: str

    @staticmethod
    def resolve_project_name(card):
        return card.project.name

    @staticmethod
    def resolve_client_name(card):
        return card.project.client.name


class RunningTimerOut(Schema):
    id: int
    card_id: int
    card_number: int
    card_title: str
    project_id: int
    project_name: str
    user: UserOut
    started_at: datetime
    mine: bool

    @staticmethod
    def resolve_card_number(entry):
        return entry.card.number

    @staticmethod
    def resolve_card_title(entry):
        return entry.card.title

    @staticmethod
    def resolve_project_id(entry):
        return entry.card.project_id

    @staticmethod
    def resolve_project_name(entry):
        return entry.card.project.name


class TotalsOut(Schema):
    clients: int
    projects: int
    open_cards: int
    running_timers: int


class OverviewOut(Schema):
    by_column: list[ColumnCountOut]
    in_progress: list[DashboardCardOut]
    running_timers: list[RunningTimerOut]
    totals: TotalsOut


class ActivityItemOut(Schema):
    kind: str  # created, moved, comment, time
    card_id: int
    card_number: int
    card_title: str
    project_id: int
    project_name: str
    user: UserOut | None
    data: dict
    created: datetime


class DeadlinesOut(Schema):
    overdue: list[DashboardCardOut]
    upcoming: list[DashboardCardOut]


class HeatmapDayOut(Schema):
    date: date
    hours: float
    level: int


class HeatmapOut(Schema):
    weeks: int
    days: list[HeatmapDayOut]
    total_hours: float


class ProjectHoursOut(Schema):
    project_id: int
    project_name: str
    client_name: str
    hours: float


class WeekOut(Schema):
    start: date
    end: date
    total_hours: float
    by_project: list[ProjectHoursOut]
