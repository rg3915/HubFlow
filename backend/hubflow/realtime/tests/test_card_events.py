import pytest

from hubflow.boards.models import Card
from hubflow.realtime.events import subscribe

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


def test_criar_card_publica_card_created(api, loja):
    with subscribe(loja.id) as events:
        response = api.post(f'/api/projects/{loja.id}/cards', {'title': 'Novo'}, **JSON)
        event = next(events)

    assert event['type'] == 'card_created'
    assert event['data']['card']['id'] == response.json()['id']
    assert event['data']['card']['title'] == 'Novo'


def test_mover_publica_card_moved_com_origem_e_destino(api, loja, card):
    with subscribe(loja.id) as events:
        api.post(f'/api/cards/{card.id}/move', {'column': 'qa', 'position': 0}, **JSON)
        event = next(events)

    assert event['type'] == 'card_moved'
    expected = {
        'card_id': card.id,
        'from_column': 'backlog',
        'to_column': 'qa',
        'position': 0,
        'by': 'ana@example.com',
    }
    assert event['data'] == expected


def test_reordenar_tambem_publica(api, loja, card):
    Card.objects.create(project=loja, title='Outro')
    with subscribe(loja.id) as events:
        api.post(f'/api/cards/{card.id}/move', {'column': 'backlog', 'position': 1}, **JSON)
        event = next(events)

    assert event['type'] == 'card_moved' and event['data']['position'] == 1


def test_editar_publica_card_updated(api, loja, card):
    with subscribe(loja.id) as events:
        api.put(f'/api/cards/{card.id}', {'title': 'Editado'}, **JSON)
        event = next(events)

    assert event['type'] == 'card_updated' and event['data']['card']['title'] == 'Editado'


def test_excluir_publica_card_deleted(api, loja, card):
    with subscribe(loja.id) as events:
        api.delete(f'/api/cards/{card.id}')
        event = next(events)

    assert event == {
        'type': 'card_deleted',
        'project_id': loja.id,
        'data': {'card_id': card.id, 'by': 'ana@example.com'},
    }


def test_etiquetas_e_checklist_publicam_card_updated(api, loja, card):
    label = api.post(f'/api/projects/{loja.id}/labels', {'name': 'bug', 'color': '#a33a2e'}, **JSON).json()
    with subscribe(loja.id) as events:
        api.put(f'/api/cards/{card.id}/labels', {'label_ids': [label['id']]}, **JSON)
        first = next(events)
        api.post(f'/api/cards/{card.id}/checklist', {'text': 'item'}, **JSON)
        second = next(events)

    assert first['type'] == 'card_updated' and [lb['name'] for lb in first['data']['card']['labels']] == ['bug']
    assert second['type'] == 'card_updated' and second['data']['card']['checklist']['total'] == 1


def test_evento_leva_quem_fez(api, loja, card):
    with subscribe(loja.id) as events:
        api.post(f'/api/cards/{card.id}/start')
        event = next(events)

    assert event['data']['by'] == 'ana@example.com'
