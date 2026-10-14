import pytest

from hubflow.boards.models import Card

pytestmark = pytest.mark.django_db


def test_cria_card_no_backlog(api, loja, user):
    data = {'title': 'Corrigir login', 'description': 'Erro 500'}
    response = api.post(f'/api/projects/{loja.id}/cards', data, content_type='application/json')

    assert response.status_code == 201
    data = response.json()
    assert data['number'] == 1
    assert (data['column'], data['position']) == ('backlog', 0)
    assert Card.objects.get(id=data['id']).created_by == user


def test_titulo_vazio_retorna_422(api, loja):
    response = api.post(f'/api/projects/{loja.id}/cards', {'title': ''}, content_type='application/json')

    assert response.status_code == 422


def test_projeto_inexistente_retorna_404(api):
    response = api.post('/api/projects/999/cards', {'title': 'X'}, content_type='application/json')

    assert response.status_code == 404


def test_quadro_devolve_as_colunas_na_ordem_com_os_cards(api, loja):
    a = Card.objects.create(project=loja, title='A')
    b = Card.objects.create(project=loja, title='B')
    Card.objects.filter(id=b.id).update(column='doing')

    response = api.get(f'/api/projects/{loja.id}/board')

    assert response.status_code == 200
    board = response.json()
    assert [c['key'] for c in board['columns']] == ['backlog', 'sprint', 'doing', 'qa', 'done', 'archived']
    assert board['columns'][0]['label'] == 'Backlog'
    assert [c['title'] for c in board['columns'][0]['cards']] == ['A']
    assert [c['title'] for c in board['columns'][2]['cards']] == ['B']
    assert board['columns'][0]['cards'][0]['id'] == a.id


def test_quadro_ordena_cards_pela_posicao(api, loja):
    first = Card.objects.create(project=loja, title='Primeiro')
    second = Card.objects.create(project=loja, title='Segundo')
    Card.objects.filter(id=first.id).update(position=5)

    response = api.get(f'/api/projects/{loja.id}/board')

    assert [c['id'] for c in response.json()['columns'][0]['cards']] == [second.id, first.id]


def test_quadro_esconde_arquivados_por_padrao(api, loja):
    # RN-37
    card = Card.objects.create(project=loja, title='Velho')
    Card.objects.filter(id=card.id).update(column='archived')

    board = api.get(f'/api/projects/{loja.id}/board').json()
    with_archived = api.get(f'/api/projects/{loja.id}/board?archived=true').json()

    assert board['columns'][5]['cards'] == []
    assert [c['title'] for c in with_archived['columns'][5]['cards']] == ['Velho']


def test_quadro_traz_dados_do_projeto(api, loja):
    board = api.get(f'/api/projects/{loja.id}/board').json()

    assert board['project'] == {'id': loja.id, 'name': 'Loja', 'client_name': 'ACME'}


def test_quadro_traz_o_criador_do_card(api, loja, user):
    api.post(f'/api/projects/{loja.id}/cards', {'title': 'Com dono'}, content_type='application/json')
    Card.objects.create(project=loja, title='Sem dono')

    cards = api.get(f'/api/projects/{loja.id}/board').json()['columns'][0]['cards']

    assert cards[0]['created_by']['id'] == user.id
    assert cards[0]['created_by']['first_name'] == 'Ana'
    assert cards[1]['created_by'] is None
