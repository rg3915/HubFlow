import pytest

from hubflow.boards.models import Card, CardMove

pytestmark = pytest.mark.django_db


def test_iniciar_move_para_em_desenvolvimento(api, loja, card):
    # RN-36
    response = api.post(f'/api/cards/{card.id}/start')

    assert response.status_code == 200
    assert response.json()['column'] == 'doing'
    card.refresh_from_db()
    assert (card.column, card.position) == ('doing', 0)


def test_iniciar_vai_para_o_fim_de_em_desenvolvimento(api, loja, card):
    Card.objects.create(project=loja, title='Outro', column='doing')

    api.post(f'/api/cards/{card.id}/start')

    card.refresh_from_db()
    assert card.position == 1


def test_movimentacao_fica_registrada(api, loja, card, user):
    # RN-35
    api.post(f'/api/cards/{card.id}/move', {'column': 'qa'}, content_type='application/json')

    move = CardMove.objects.get(card=card)
    assert (move.from_column, move.to_column, move.user) == ('backlog', 'qa', user)
    assert move.created is not None


def test_iniciar_tambem_registra(api, loja, card):
    api.post(f'/api/cards/{card.id}/start')

    assert CardMove.objects.filter(card=card, to_column='doing').exists()


def test_reordenar_na_mesma_coluna_nao_registra(api, loja, card):
    Card.objects.create(project=loja, title='Outro')

    api.post(f'/api/cards/{card.id}/move', {'column': 'backlog', 'position': 1}, content_type='application/json')

    assert CardMove.objects.count() == 0


def test_historico_do_card(api, loja, card):
    api.post(f'/api/cards/{card.id}/start')
    api.post(f'/api/cards/{card.id}/move', {'column': 'qa'}, content_type='application/json')

    response = api.get(f'/api/cards/{card.id}/history')

    assert response.status_code == 200
    history = response.json()
    assert [(h['from_column'], h['to_column']) for h in history] == [('doing', 'qa'), ('backlog', 'doing')]
    assert history[0]['user_email'] == 'ana@example.com'
