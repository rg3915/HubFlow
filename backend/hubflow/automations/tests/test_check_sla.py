from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone

from hubflow.automations.models import Automation, ColumnSla
from hubflow.automations.services import check_deadlines_and_sla
from hubflow.boards.models import Card, CardEvent, Notification
from hubflow.boards.services import move_card

pytestmark = pytest.mark.django_db


@pytest.fixture
def late_card(loja, user):
    ColumnSla.objects.create(project=loja, column='qa', hours=24)
    card = Card.objects.create(project=loja, title='Parado em QA', column='qa', created_by=user)
    Card.objects.filter(id=card.id).update(column_entered_at=timezone.now() - timedelta(hours=30))
    return card


def test_sla_estourado_dispara_o_gatilho_uma_vez(loja, late_card):
    Automation.objects.create(
        project=loja, name='Escalar', trigger='sla_breached', action='move', action_column='doing'
    )

    assert check_deadlines_and_sla()['sla'] == 1
    assert check_deadlines_and_sla()['sla'] == 0  # não repete

    late_card.refresh_from_db()
    assert late_card.column == 'doing'
    assert CardEvent.objects.filter(card=late_card, kind='sla_breached', data__column='qa').exists()


def test_voltar_para_a_coluna_reabre_a_contagem(loja, late_card):
    check_deadlines_and_sla()
    move_card(late_card, 'doing')
    move_card(late_card, 'qa')
    Card.objects.filter(id=late_card.id).update(column_entered_at=timezone.now() - timedelta(hours=30))

    assert check_deadlines_and_sla()['sla'] == 1


def test_dentro_do_sla_ou_concluido_nao_dispara(loja, user):
    ColumnSla.objects.create(project=loja, column='qa', hours=24)
    ColumnSla.objects.create(project=loja, column='done', hours=1)
    Card.objects.create(project=loja, title='Recente', column='qa')
    done = Card.objects.create(project=loja, title='Feito', column='done')
    Card.objects.filter(id=done.id).update(column_entered_at=timezone.now() - timedelta(hours=5))

    assert check_deadlines_and_sla()['sla'] == 0


def test_prazo_vencido_avisa_o_responsavel_uma_vez_por_prazo(loja, user):
    bob = get_user_model().objects.create_user(email='bob@hubflow.com', password='x', name='Bob')
    today = timezone.localdate()
    card = Card.objects.create(project=loja, title='Atrasado', assignee=bob, due_date=today - timedelta(days=1))
    Card.objects.create(project=loja, title='Em dia', assignee=bob, due_date=today + timedelta(days=1))
    Card.objects.create(project=loja, title='Feito', assignee=bob, due_date=today - timedelta(days=3), column='done')

    assert check_deadlines_and_sla()['overdue'] == 1
    assert check_deadlines_and_sla()['overdue'] == 0
    note = Notification.objects.get(user=bob)
    assert note.kind == 'overdue' and f'#{card.number}' in note.text

    card.due_date = today - timedelta(days=2)  # prazo mudou: avisa de novo
    card.save()
    assert check_deadlines_and_sla()['overdue'] == 1


def test_comando(late_card, capsys):
    call_command('check_sla')

    assert 'SLA estourado: 1' in capsys.readouterr().out
