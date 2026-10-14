from ninja import Field, ModelSchema, Schema

from .models import Automation


class AutomationIn(Schema):
    name: str = Field(min_length=1, max_length=100)
    is_active: bool = True
    trigger: str
    trigger_column: str = ''
    action: str
    action_column: str = ''
    action_user_id: int | None = None
    action_label_id: int | None = None


class AutomationOut(ModelSchema):
    project_id: int
    action_user_id: int | None
    action_label_id: int | None
    description: str

    class Meta:
        model = Automation
        fields = ['id', 'uuid', 'name', 'is_active', 'trigger', 'trigger_column', 'action', 'action_column']

    @staticmethod
    def resolve_description(rule):
        return rule.describe()
