import pytest

from hubflow.boards.models import ChecklistItem

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


def add_item(api, card, text):
    return api.post(f'/api/cards/{card.id}/checklist', {'text': text}, **JSON)


def test_adiciona_item_no_fim(api, card):
    first = add_item(api, card, 'Escrever teste')
    second = add_item(api, card, 'Implementar')

    assert first.status_code == 201
    assert (first.json()['position'], first.json()['done']) == (0, False)
    assert second.json()['position'] == 1


def test_texto_vazio_retorna_422(api, card):
    assert add_item(api, card, ' ').status_code == 422


def test_lista_itens_na_ordem(api, card):
    add_item(api, card, 'A')
    add_item(api, card, 'B')

    response = api.get(f'/api/cards/{card.id}/checklist')

    assert [i['text'] for i in response.json()] == ['A', 'B']


def test_marca_e_desmarca_item(api, card):
    item_id = add_item(api, card, 'A').json()['id']

    response = api.put(f'/api/checklist/{item_id}', {'text': 'A', 'done': True}, **JSON)

    assert response.status_code == 200
    assert ChecklistItem.objects.get(id=item_id).done is True


def test_exclui_item_e_reordena(api, card):
    first = add_item(api, card, 'A').json()['id']
    second = add_item(api, card, 'B').json()['id']

    assert api.delete(f'/api/checklist/{first}').status_code == 204
    assert ChecklistItem.objects.get(id=second).position == 0


def test_reordena_itens(api, card):
    a = add_item(api, card, 'A').json()['id']
    b = add_item(api, card, 'B').json()['id']
    c = add_item(api, card, 'C').json()['id']

    response = api.put(f'/api/cards/{card.id}/checklist/order', {'item_ids': [c, a, b]}, **JSON)

    assert response.status_code == 200
    assert [i['text'] for i in api.get(f'/api/cards/{card.id}/checklist').json()] == ['C', 'A', 'B']


def test_reordenar_com_item_de_outro_card_retorna_400(api, loja, card):
    from hubflow.boards.models import Card

    other = Card.objects.create(project=loja, title='Outro')
    foreign = add_item(api, other, 'X').json()['id']
    a = add_item(api, card, 'A').json()['id']

    response = api.put(f'/api/cards/{card.id}/checklist/order', {'item_ids': [foreign, a]}, **JSON)

    assert response.status_code == 400


def test_card_traz_contagem_do_checklist(api, loja, card):
    a = add_item(api, card, 'A').json()['id']
    add_item(api, card, 'B')
    api.put(f'/api/checklist/{a}', {'text': 'A', 'done': True}, **JSON)

    data = api.get(f'/api/cards/{card.id}').json()
    board_card = api.get(f'/api/projects/{loja.id}/board').json()['columns'][0]['cards'][0]

    assert data['checklist'] == {'done': 1, 'total': 2}
    assert board_card['checklist'] == {'done': 1, 'total': 2}
