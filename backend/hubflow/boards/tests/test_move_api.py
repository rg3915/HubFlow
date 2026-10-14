import pytest

from hubflow.boards.models import Card

pytestmark = pytest.mark.django_db


@pytest.fixture
def cards(loja):
    """Três cards no backlog (posições 0, 1, 2) e um em QA."""
    a = Card.objects.create(project=loja, title='A')
    b = Card.objects.create(project=loja, title='B')
    c = Card.objects.create(project=loja, title='C')
    q = Card.objects.create(project=loja, title='Q', column='qa')
    return {'a': a, 'b': b, 'c': c, 'q': q}


def move(api, card, **data):
    return api.post(f'/api/cards/{card.id}/move', data, content_type='application/json')


def positions(project, column):
    return list(project.cards.filter(column=column).order_by('position').values_list('title', 'position'))


def test_move_para_outra_coluna_no_fim_por_padrao(api, loja, cards):
    # RN-34
    response = move(api, cards['b'], column='qa')

    assert response.status_code == 200
    assert response.json()['column'] == 'qa'
    assert positions(loja, 'qa') == [('Q', 0), ('B', 1)]
    # RN-33: a coluna de origem fecha o buraco.
    assert positions(loja, 'backlog') == [('A', 0), ('C', 1)]


def test_move_para_posicao_especifica(api, loja, cards):
    move(api, cards['c'], column='qa', position=0)

    assert positions(loja, 'qa') == [('C', 0), ('Q', 1)]


def test_reordena_dentro_da_mesma_coluna(api, loja, cards):
    move(api, cards['a'], column='backlog', position=2)

    assert positions(loja, 'backlog') == [('B', 0), ('C', 1), ('A', 2)]


def test_posicao_acima_do_fim_vai_para_o_fim(api, loja, cards):
    move(api, cards['a'], column='qa', position=99)

    assert positions(loja, 'qa') == [('Q', 0), ('A', 1)]


def test_coluna_invalida_retorna_422(api, cards):
    assert move(api, cards['a'], column='limbo').status_code == 422


def test_card_inexistente_retorna_404(api, loja):
    response = api.post('/api/cards/999/move', {'column': 'qa'}, content_type='application/json')

    assert response.status_code == 404


def test_qualquer_coluna_pode_ir_para_qualquer_outra(api, loja, cards):
    # RN-35: não há transição proibida.
    assert move(api, cards['q'], column='archived').status_code == 200
    assert move(api, cards['q'], column='backlog').status_code == 200
