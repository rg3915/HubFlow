import pytest

from hubflow.boards.models import Card

pytestmark = pytest.mark.django_db


def test_detalhe_do_card(api, card):
    response = api.get(f'/api/cards/{card.id}')

    assert response.status_code == 200
    assert response.json()['title'] == 'Corrigir login'


def test_card_inexistente_retorna_404(api, loja):
    assert api.get('/api/cards/999').status_code == 404


def test_edita_titulo_e_descricao(api, card):
    data = {'title': 'Corrigir login no celular', 'description': 'Só no Safari'}

    response = api.put(f'/api/cards/{card.id}', data, content_type='application/json')

    assert response.status_code == 200
    card.refresh_from_db()
    assert (card.title, card.description) == ('Corrigir login no celular', 'Só no Safari')


def test_editar_nao_muda_coluna_nem_posicao(api, loja, card):
    api.post(f'/api/cards/{card.id}/start')

    api.put(f'/api/cards/{card.id}', {'title': 'Novo título'}, content_type='application/json')

    card.refresh_from_db()
    assert card.column == 'doing'


def test_titulo_vazio_na_edicao_retorna_422(api, card):
    assert api.put(f'/api/cards/{card.id}', {'title': '  '}, content_type='application/json').status_code == 422


def test_exclui_card_e_fecha_o_buraco(api, loja, card):
    other = Card.objects.create(project=loja, title='Outro')

    response = api.delete(f'/api/cards/{card.id}')

    assert response.status_code == 204
    assert not Card.objects.filter(id=card.id).exists()
    other.refresh_from_db()
    assert other.position == 0


def test_arquiva_card(api, loja, card):
    response = api.post(f'/api/cards/{card.id}/archive')

    assert response.status_code == 200
    card.refresh_from_db()
    assert card.column == 'archived'


def test_excluir_projeto_arquiva_os_cards(api, loja, card):
    # RN-24
    response = api.delete(f'/api/projects/{loja.id}')

    assert response.status_code == 204
    card.refresh_from_db()
    assert card.column == 'archived'
    loja.refresh_from_db()
    assert loja.is_active is False
