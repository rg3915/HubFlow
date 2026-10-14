import pytest
from django.contrib.auth import get_user_model
from django.core import mail

from hubflow.boards.models import Comment

pytestmark = pytest.mark.django_db

User = get_user_model()


@pytest.fixture
def bob(db):
    return User.objects.create_user(email='bob@example.com', password='segredo123', name='Bob Silva')


def post_comment(api, card, text):
    return api.post(f'/api/cards/{card.id}/comments', {'text': text}, content_type='application/json')


def test_lista_usuarios_para_autocompletar(api, user, bob):
    response = api.get('/api/users')

    assert response.status_code == 200
    assert [u['email'] for u in response.json()] == ['ana@example.com', 'bob@example.com']
    assert response.json()[1]['name'] == 'Bob Silva'


def test_usuarios_inativos_nao_aparecem(api, user, bob):
    bob.is_active = False
    bob.save()

    assert [u['email'] for u in api.get('/api/users').json()] == ['ana@example.com']


def test_mencao_por_email_avisa_o_mencionado(api, card, bob, settings):
    settings.FRONTEND_URL = 'http://app.test'
    mail.outbox.clear()

    response = post_comment(api, card, 'Olha isso, @bob@example.com')

    assert response.json()['mentions'] == [{'id': bob.id, 'email': 'bob@example.com', 'name': 'Bob Silva'}]
    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ['bob@example.com']
    assert 'Ana' in message.subject and '#1' in message.subject
    assert 'Olha isso' in message.body and 'http://app.test/projects/' in message.body


def test_mencao_por_nome(api, card, bob):
    mail.outbox.clear()

    post_comment(api, card, 'Pode ver, @Bob?')

    assert mail.outbox[0].to == ['bob@example.com']


def test_mencao_nao_diferencia_maiusculas_e_nao_repete(api, card, bob):
    mail.outbox.clear()

    response = post_comment(api, card, '@BOB e @bob@example.com de novo')

    assert len(response.json()['mentions']) == 1
    assert len(mail.outbox) == 1


def test_mencionar_a_si_mesmo_nao_avisa(api, card, user):
    mail.outbox.clear()

    post_comment(api, card, 'nota para mim @ana')

    assert mail.outbox == []


def test_mencao_desconhecida_e_ignorada(api, card):
    mail.outbox.clear()

    response = post_comment(api, card, 'ping @ninguem')

    assert response.status_code == 201
    assert response.json()['mentions'] == []
    assert mail.outbox == []


def test_mencoes_ficam_guardadas(api, card, bob):
    comment_id = post_comment(api, card, 'oi @bob').json()['id']

    assert list(Comment.objects.get(id=comment_id).mentions.all()) == [bob]
