import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from hubflow.realtime import broadcast
from hubflow.sprints.models import Sprint

from .activity import record
from .models import Card, CardMove, Column
from .notifications import actor_name, card_owners, notify, notify_in_app

logger = logging.getLogger(__name__)
CLOSED_COLUMNS = (Column.DONE, Column.ARCHIVED)


def resolve_sprint(project, sprint=None):
    """RN-61: sprint informada → usa; senão a última aberta; se não houver, cria a próxima."""
    if sprint is not None:
        return sprint
    return Sprint.objects.latest_open(project) or Sprint.objects.create(project=project)


def create_card(project, user=None, **data):
    """Cria o card no Backlog (RN-31), na sprint certa (RN-61), avisa os destinatários e, se o projeto pedir,
    abre a issue no repositório (falha remota não impede o card)."""
    data['sprint'] = resolve_sprint(project, data.get('sprint'))
    card = Card.objects.create(project=project, created_by=user, **data)
    record(card, 'created', user)
    if project.create_issues:
        mirror_issue(card)
    notify('created', card)
    broadcast.card_created(card, user)
    return card


def with_repo(card, action, *args):
    """Executa `action(client, *args)` no repositório do card; falha remota só gera aviso."""
    from hubflow.integrations.client import RepoClient, RepoError

    try:
        return action(RepoClient(card.project), *args)
    except RepoError as error:
        logger.warning('Card #%s de %s: repositório não atualizado: %s', card.number, card.project, error)
        return None


def mirror_issue(card):
    result = with_repo(card, lambda client: client.create_issue(card.title, card.description))
    if result:
        card.issue_number, card.issue_url = result
        card.save(update_fields=['issue_number', 'issue_url'])


def sync_issue_fields(card):
    """Título e descrição do card vão para a issue, se houver."""
    if card.issue_number:
        with_repo(card, lambda client: client.update_issue(card.issue_number, card.title, card.description))


def sync_issue_state(card, from_column, to_column):
    """Concluído/Arquivadas fecha a issue; sair delas reabre."""
    if not card.issue_number:
        return
    was_closed, is_closed = from_column in CLOSED_COLUMNS, to_column in CLOSED_COLUMNS
    if was_closed != is_closed:
        with_repo(card, lambda client: client.set_issue_state(card.issue_number, is_closed))


def resolve_assignee(assignee_id):
    """Devolve o usuário responsável ou 404; None quando o card fica sem responsável."""
    if assignee_id is None:
        return None
    return get_object_or_404(get_user_model(), id=assignee_id, is_active=True)


def renumber(items):
    """Deixa as posições consecutivas a partir de 0, na ordem recebida (RN-33). Serve a cards e itens de checklist."""
    for index, item in enumerate(items):
        item.position = index
    if items:
        type(items[0]).objects.bulk_update(items, ['position'])


def card_queryset():
    """Cards com tudo o que a API devolve, sem consultas extras por card."""
    return (
        Card.objects.select_related('assignee', 'created_by')
        .prefetch_related('labels')
        .annotate(
            checklist_total=Count('checklist_items', distinct=True),
            checklist_done=Count('checklist_items', filter=Q(checklist_items__done=True), distinct=True),
        )
    )


@transaction.atomic
def move_card(card, column, position=None, user=None, sync=True):
    """Move o card para a coluna/posição e reordena origem e destino (RN-33, RN-34).

    É o único caminho para mudar a coluna de um card: API, CLI e automações passam por aqui.
    """
    siblings = Card.objects.select_for_update().filter(project_id=card.project_id).exclude(id=card.id)
    source = list(siblings.filter(column=card.column).order_by('position', 'id'))
    target = source if column == card.column else list(siblings.filter(column=column).order_by('position', 'id'))

    position = len(target) if position is None else max(0, min(position, len(target)))
    target.insert(position, card)
    from_column = card.column
    if column != from_column:
        CardMove.objects.create(card=card, from_column=from_column, to_column=column, user=user)
    card.column = column
    renumber(target)
    if source is not target:
        renumber(source)
    card.save(update_fields=['column', 'modified'])
    if sync:
        sync_issue_state(card, from_column, column)
    broadcast.card_moved(card, from_column, column, user)
    if column != from_column:
        text = f'{actor_name(user)} moveu #{card.number} {card.title} para {Column(column).label}'
        notify_in_app(card_owners(card), 'moved', card, text, user)
    if column == Column.DONE:
        notify('done', card)
    elif column not in (from_column, Column.ARCHIVED):
        notify('moved', card, from_column=from_column, to_column=column)
    return card


def start_card(card, user=None):
    # RN-36
    return move_card(card, Column.DOING, user=user)


@transaction.atomic
def delete_card(card, user=None):
    """Exclui o card e fecha o buraco na coluna (RN-33)."""
    column, project_id, card_id = card.column, card.project_id, card.id
    card.delete()
    renumber(list(Card.objects.filter(project_id=project_id, column=column).order_by('position', 'id')))
    broadcast.card_deleted(project_id, card_id, user)


@transaction.atomic
def archive_project(project, user=None):
    """RN-24: excluir um projeto arquiva os cards e desativa o projeto, sem apagar nada."""
    for card in project.cards.exclude(column=Column.ARCHIVED).order_by('column', 'position'):
        move_card(card, Column.ARCHIVED, user=user)
    project.is_active = False
    project.save(update_fields=['is_active', 'modified'])
