import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.boards.models import Card, Notification

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
User = get_user_model()


@pytest.fixture
def bob(db):
    bob = User.objects.create_user(email='bob@hubflow.com', password='x', name='Bob Silva')
    bob.groups.add(Group.objects.get(name='Administrador'))
    return bob


def api_for(user):
    return HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=user).key}'})


def comment(api, card, text):
    return api.post(f'/api/cards/{card.id}/comments', {'text': text}, **JSON)


def test_mencao_gera_notificacao(api, loja, user, bob):
    card = Card.objects.create(project=loja, title='Login', created_by=user)

    comment(api, card, 'Olha isso, @bob')

    note = Notification.objects.get(user=bob)
    assert (note.kind, note.card, note.actor, note.read_at) == ('mention', card, user, None)
    assert 'Ana' in note.text


def test_comentario_em_card_seu_ou_de_que_e_responsavel(api, loja, user, bob):
    carol = User.objects.create_user(email='carol@hubflow.com', password='x', name='Carol')
    card = Card.objects.create(project=loja, title='Login', created_by=bob, assignee=carol)

    comment(api, card, 'Reproduzi.')

    assert sorted(Notification.objects.filter(kind='comment').values_list('user__email', flat=True)) == [
        'bob@hubflow.com',
        'carol@hubflow.com',
    ]
    assert not Notification.objects.filter(user=user).exists()  # quem comentou não se notifica


def test_mencionado_dono_recebe_uma_so(api, loja, user, bob):
    card = Card.objects.create(project=loja, title='Login', created_by=bob)

    comment(api, card, '@bob veja')

    assert list(Notification.objects.filter(user=bob).values_list('kind', flat=True)) == ['mention']


def test_card_seu_movido_por_outro(api, loja, user, bob):
    card = Card.objects.create(project=loja, title='Login', created_by=bob)

    api.post(f'/api/cards/{card.id}/move', {'column': 'qa'}, **JSON)

    note = Notification.objects.get(user=bob)
    assert note.kind == 'moved' and 'QA' in note.text


def test_mover_o_proprio_card_nao_notifica(api, loja, user):
    card = Card.objects.create(project=loja, title='Login', created_by=user)

    api.post(f'/api/cards/{card.id}/move', {'column': 'qa'}, **JSON)

    assert not Notification.objects.exists()


def test_api_lista_nao_lidas_primeiro_e_marca_como_lidas(api, loja, user, bob):
    card = Card.objects.create(project=loja, title='Login', created_by=bob)
    comment(api, card, 'primeiro')
    comment(api, card, 'segundo')
    bob_api = api_for(bob)
    first, second = Notification.objects.filter(user=bob).order_by('created')

    assert bob_api.post(f'/api/notifications/{first.id}/read').status_code == 200
    data = bob_api.get('/api/notifications').json()

    assert data['unread'] == 1
    assert [n['id'] for n in data['items']] == [second.id, first.id]
    item = data['items'][0]
    assert item['card_number'] == card.number and item['project_id'] == loja.id and item['read'] is False
    assert item['actor_name'] == 'Ana' and item['card_title'] == 'Login'

    assert bob_api.post('/api/notifications/read-all').json()['unread'] == 0
    assert api.post(f'/api/notifications/{first.id}/read').status_code == 404  # notificação de outra pessoa
