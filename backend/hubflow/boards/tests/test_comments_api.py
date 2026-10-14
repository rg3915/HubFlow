import pytest
from django.contrib.auth import get_user_model
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.boards.models import Comment

pytestmark = pytest.mark.django_db


def post_comment(api, card, text):
    return api.post(f'/api/cards/{card.id}/comments', {'text': text}, content_type='application/json')


def test_cria_comentario(api, card, user):
    response = post_comment(api, card, 'Reproduzi o erro no Safari.')

    assert response.status_code == 201
    data = response.json()
    assert data['text'] == 'Reproduzi o erro no Safari.'
    assert data['author'] == {
        'id': user.id,
        'uuid': str(user.uuid),
        'email': 'ana@example.com',
        'name': 'Ana',
        'first_name': 'Ana',
        'avatar_url': None,
    }
    assert Comment.objects.get(id=data['id']).card == card


def test_comentario_vazio_retorna_422(api, card):
    assert post_comment(api, card, '   ').status_code == 422


def test_lista_comentarios_em_ordem_cronologica(api, card):
    post_comment(api, card, 'Primeiro')
    post_comment(api, card, 'Segundo')

    response = api.get(f'/api/cards/{card.id}/comments')

    assert response.status_code == 200
    assert [c['text'] for c in response.json()] == ['Primeiro', 'Segundo']


def test_autor_edita_o_proprio_comentario(api, card):
    comment_id = post_comment(api, card, 'Errado').json()['id']

    response = api.put(f'/api/comments/{comment_id}', {'text': 'Certo'}, content_type='application/json')

    assert response.status_code == 200
    assert Comment.objects.get(id=comment_id).text == 'Certo'


def test_autor_exclui_o_proprio_comentario(api, card):
    comment_id = post_comment(api, card, 'Apagar').json()['id']

    response = api.delete(f'/api/comments/{comment_id}')

    assert response.status_code == 204
    assert not Comment.objects.filter(id=comment_id).exists()


def test_outro_usuario_nao_edita_nem_exclui(api, card):
    comment_id = post_comment(api, card, 'Da Ana').json()['id']
    other = get_user_model().objects.create_user(email='bob@example.com', password='segredo123')
    other_api = HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=other).key}'})

    response = other_api.put(f'/api/comments/{comment_id}', {'text': 'x'}, content_type='application/json')

    assert response.status_code == 403
    assert other_api.delete(f'/api/comments/{comment_id}').status_code == 403
    assert Comment.objects.get(id=comment_id).text == 'Da Ana'


def test_card_inexistente_retorna_404(api, loja):
    response = api.post('/api/cards/999/comments', {'text': 'x'}, content_type='application/json')

    assert response.status_code == 404
