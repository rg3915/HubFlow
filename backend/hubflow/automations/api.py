from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from ninja import Body, Router, Status

from hubflow.accounts.schemas import DetailOut
from hubflow.boards.models import Column, Label
from hubflow.permissions.services import require, visible_in_project_or_404, visible_project_or_404

from .models import Automation, ColumnSla
from .schemas import AutomationIn, AutomationOut

router = Router(tags=['automations'])


def rules():
    return Automation.objects.select_related('action_user', 'action_label')


def save_rule(rule, data):
    """Aplica os dados, valida (incluindo responsável e etiqueta existentes) e salva; 400 se algo não serve."""
    for field, value in data.dict().items():
        setattr(rule, field, value)
    if data.action_user_id and not get_user_model().objects.filter(id=data.action_user_id, is_active=True).exists():
        return Status(400, {'detail': 'Responsável não encontrado.'})
    if data.action_label_id and not Label.objects.filter(id=data.action_label_id).exists():
        return Status(400, {'detail': 'Etiqueta não encontrada.'})
    try:
        rule.full_clean(exclude=['project', 'uuid', 'created_by'])
    except ValidationError as error:
        return Status(400, {'detail': ' '.join(error.messages)})
    rule.save()
    return None


@router.get('/projects/{project_id}/automations', response=list[AutomationOut])
def list_automations(request, project_id: int):
    return rules().filter(project=visible_project_or_404(request.user, project_id))


@router.post('/projects/{project_id}/automations', response={201: AutomationOut, 400: DetailOut})
def add_automation(request, project_id: int, data: AutomationIn):
    project = visible_project_or_404(request.user, project_id)
    require(request.user, 'projects.change_project')
    rule = Automation(project=project, created_by=request.user)
    return save_rule(rule, data) or Status(201, rule)


def editable_rule(request, rule_id):
    rule = visible_in_project_or_404(request.user, rules(), id=rule_id)
    require(request.user, 'projects.change_project')
    return rule


@router.put('/automations/{rule_id}', response={200: AutomationOut, 400: DetailOut})
def update_automation(request, rule_id: int, data: AutomationIn):
    rule = editable_rule(request, rule_id)
    return save_rule(rule, data) or rule


@router.delete('/automations/{rule_id}', response={204: None})
def delete_automation(request, rule_id: int):
    editable_rule(request, rule_id).delete()
    return Status(204, None)


def sla_map(project):
    hours = dict(project.column_slas.values_list('column', 'hours'))
    return {column: hours.get(column) for column in Column.values}


@router.get('/projects/{project_id}/sla', response=dict[str, int | None])
def get_sla(request, project_id: int):
    return sla_map(visible_project_or_404(request.user, project_id))


@router.put('/projects/{project_id}/sla', response={200: dict[str, int | None], 400: DetailOut})
def set_sla(request, project_id: int, data: dict[str, int | None] = Body(...)):
    """{coluna: horas}; null tira o SLA da coluna. Colunas não enviadas ficam como estão."""
    project = visible_project_or_404(request.user, project_id)
    require(request.user, 'projects.change_project')
    unknown = set(data) - set(Column.values)
    if unknown:
        return Status(400, {'detail': f'Coluna desconhecida: {", ".join(sorted(unknown))}.'})
    if any(hours is not None and hours < 1 for hours in data.values()):
        return Status(400, {'detail': 'O SLA é em horas inteiras, a partir de 1.'})
    for column, hours in data.items():
        if hours is None:
            project.column_slas.filter(column=column).delete()
        else:
            ColumnSla.objects.update_or_create(project=project, column=column, defaults={'hours': hours})
    return sla_map(project)
