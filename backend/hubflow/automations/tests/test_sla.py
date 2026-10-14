from datetime import timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from hubflow.automations.models import ColumnSla
from hubflow.boards.models import Card

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


def board_cards(api, loja):
    return {c['id']: c for col in api.get(f'/api/projects/{loja.id}/board').json()['columns'] for c in col['cards']}


def test_define_e_le_o_sla_das_colunas(api, loja):
    response = api.put(f'/api/projects/{loja.id}/sla', {'qa': 48, 'doing': 24}, **JSON)

    assert response.status_code == 200
    expected = {'backlog': None, 'sprint': None, 'doing': 24, 'qa': 48, 'done': None, 'archived': None}
    assert response.json() == expected
    assert api.get(f'/api/projects/{loja.id}/sla').json() == expected
    api.put(f'/api/projects/{loja.id}/sla', {'qa': None}, **JSON)
    assert list(ColumnSla.objects.values_list('column', flat=True)) == ['doing']


def test_card_guarda_quando_entrou_na_coluna(api, loja):
    card_id = api.post(f'/api/projects/{loja.id}/cards', {'title': 'Login'}, **JSON).json()['id']
    before = timezone.now()

    api.post(f'/api/cards/{card_id}/move', {'column': 'qa'}, **JSON)

    assert Card.objects.get(id=card_id).column_entered_at >= before


def test_sla_no_card_do_quadro_estourado_ou_nao(api, loja):
    ColumnSla.objects.create(project=loja, column='qa', hours=48)
    old = Card.objects.create(project=loja, title='Velho', column='qa')
    fresh = Card.objects.create(project=loja, title='Novo', column='qa')
    Card.objects.filter(id=old.id).update(column_entered_at=timezone.now() - timedelta(hours=50))
    free = Card.objects.create(project=loja, title='Sem SLA')

    cards = board_cards(api, loja)

    assert cards[old.id]['sla']['breached'] is True and cards[old.id]['sla']['hours'] == 48
    assert cards[fresh.id]['sla']['breached'] is False
    assert cards[free.id]['sla'] is None
    assert cards[free.id]['column_entered_at']


def test_quadro_sem_n_mais_1(api, loja):
    ColumnSla.objects.create(project=loja, column='backlog', hours=1)
    Card.objects.create(project=loja, title='Um')
    with CaptureQueriesContext(connection) as one:
        api.get(f'/api/projects/{loja.id}/board')
    for i in range(5):
        Card.objects.create(project=loja, title=f'Mais {i}')
    with CaptureQueriesContext(connection) as six:
        api.get(f'/api/projects/{loja.id}/board')

    assert len(six) == len(one)


def test_horas_invalidas_ou_coluna_desconhecida(api, loja):
    assert api.put(f'/api/projects/{loja.id}/sla', {'qa': 0}, **JSON).status_code == 400
    assert api.put(f'/api/projects/{loja.id}/sla', {'teste': 4}, **JSON).status_code == 400


def test_quadro_sem_n_mais_1_com_sprint_tempo_e_anexos(api, loja, user):
    from hubflow.boards.models import Attachment
    from hubflow.sprints.models import Sprint
    from hubflow.timetracking.models import TimeEntry

    sprint = Sprint.objects.create(project=loja)

    def add_card(i):
        card = Card.objects.create(project=loja, title=f'C{i}', sprint=sprint)
        now = timezone.now()
        TimeEntry.objects.create(card=card, user=user, started_at=now - timedelta(hours=1), ended_at=now)
        Attachment.objects.create(card=card, name='a.txt', size=1, uploaded_by=user, file='a.txt')

    add_card(0)
    with CaptureQueriesContext(connection) as one:
        cards = board_cards(api, loja)
    for i in range(1, 5):
        add_card(i)
    with CaptureQueriesContext(connection) as five:
        cards = board_cards(api, loja)

    assert len(five) == len(one)
    card = next(iter(cards.values()))
    assert card['time']['hours'] == 1.0 and card['attachments_count'] == 1 and card['sprint']['number'] == 1
