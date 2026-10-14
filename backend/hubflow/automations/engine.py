"""Executa as automações do projeto nos eventos do card (RN-110)."""

from contextvars import ContextVar

_running = ContextVar('automations_running', default=False)


def run(trigger, card, column=None):
    """Roda as regras ligadas do gatilho; dentro de uma ação de automação não roda nada (sem laço)."""
    if _running.get():
        return
    from .models import Automation

    rules = Automation.objects.filter(project_id=card.project_id, is_active=True, trigger=trigger)
    if column:
        rules = rules.filter(trigger_column=column) if trigger == 'entered_column' else rules
    token = _running.set(True)
    try:
        for rule in rules.select_related('action_user', 'action_label'):
            apply(rule, card)
    finally:
        _running.reset(token)


def apply(rule, card):
    from hubflow.boards.activity import record
    from hubflow.boards.notifications import card_owners, notify_in_app
    from hubflow.boards.services import move_card

    if rule.action == 'move':
        move_card(card, rule.action_column)
    elif rule.action == 'assign':
        card.assignee = rule.action_user
        card.save(update_fields=['assignee', 'modified'])
    elif rule.action == 'add_label':
        card.labels.add(rule.action_label)
    elif rule.action == 'notify':
        notify_in_app(card_owners(card), 'automation', card, f'{rule.name}: #{card.number} {card.title}')
    record(card, 'automation', None, name=rule.name, description=rule.describe())
