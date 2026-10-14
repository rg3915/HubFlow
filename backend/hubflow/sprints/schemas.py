from datetime import date

from ninja import ModelSchema, Schema
from pydantic import field_validator

from .models import Milestone, Sprint


class MilestoneIn(Schema):
    title: str
    external_number: int | None = None

    @field_validator('title')
    @classmethod
    def titulo_obrigatorio(cls, value):
        if not value.strip():
            raise ValueError('O título é obrigatório.')
        return value.strip()


class MilestoneOut(ModelSchema):
    project_id: int

    class Meta:
        model = Milestone
        fields = ['id', 'uuid', 'title', 'external_number', 'is_open']


class SprintIn(Schema):
    name: str = ''
    milestone_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None


class SprintOut(ModelSchema):
    project_id: int
    milestone: MilestoneOut | None
    cards_count: int = 0

    class Meta:
        model = Sprint
        fields = ['id', 'uuid', 'number', 'name', 'start_date', 'end_date', 'is_open', 'closed_at']

    @staticmethod
    def resolve_cards_count(sprint):
        return getattr(sprint, 'cards_count', None) or sprint.cards.count()
