import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.boards.models import Card, Comment
from hubflow.permissions.models import Membership

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
User = get_user_model()


def api_for(user):
    return HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=user).key}'})


@pytest.fixture
def dev(loja):
    dev = User.objects.create_user(email='dev@hubflow.com', password='x', name='Dev')
    dev.groups.add(Group.objects.get(name='Desenvolvedor'))
    Membership.objects.create(user=dev, client=loja.client)
    return dev


@pytest.fixture
def reader(loja):
    reader = User.objects.create_user(email='leitura@hubflow.com', password='x', name='Leitura')
    reader.groups.add(Group.objects.get(name='Leitura'))
    Membership.objects.create(user=reader, client=loja.client)
    return reader


@pytest.fixture
def others_card(loja, user):
    return Card.objects.create(project=loja, title='Da Ana', created_by=user)


def test_leitura_nao_cria_card(loja, reader):
    response = api_for(reader).post(f'/api/projects/{loja.id}/cards', {'title': 'X'}, **JSON)

    assert response.status_code == 403
    assert 'Criar cards' in response.json()['detail']


def test_desenvolvedor_cria_card(loja, dev):
    assert api_for(dev).post(f'/api/projects/{loja.id}/cards', {'title': 'X'}, **JSON).status_code == 201


def test_desenvolvedor_edita_e_move_so_os_proprios(loja, dev, others_card):
    api = api_for(dev)
    mine = api.post(f'/api/projects/{loja.id}/cards', {'title': 'Meu'}, **JSON).json()

    assert api.put(f'/api/cards/{mine["id"]}', {'title': 'Meu editado'}, **JSON).status_code == 200
    assert api.post(f'/api/cards/{mine["id"]}/move', {'column': 'doing'}, **JSON).status_code == 200
    assert api.put(f'/api/cards/{others_card.id}', {'title': 'Hack'}, **JSON).status_code == 403
    assert api.post(f'/api/cards/{others_card.id}/move', {'column': 'done'}, **JSON).status_code == 403
    assert api.post(f'/api/cards/{others_card.id}/start').status_code == 403


def test_responsavel_tambem_conta_como_dono(loja, dev, others_card):
    others_card.assignee = dev
    others_card.save()

    assert api_for(dev).put(f'/api/cards/{others_card.id}', {'title': 'Agora é meu'}, **JSON).status_code == 200


def test_gerente_edita_qualquer_card(loja, others_card):
    manager = User.objects.create_user(email='ger@hubflow.com', password='x')
    manager.groups.add(Group.objects.get(name='Gerente'))

    assert api_for(manager).put(f'/api/cards/{others_card.id}', {'title': 'Ok'}, **JSON).status_code == 200


def test_desenvolvedor_exclui_e_arquiva_so_os_proprios(loja, dev, others_card):
    api = api_for(dev)
    mine = api.post(f'/api/projects/{loja.id}/cards', {'title': 'Meu'}, **JSON).json()

    assert api.delete(f'/api/cards/{others_card.id}').status_code == 403
    assert api.post(f'/api/cards/{others_card.id}/archive').status_code == 403
    assert api.delete(f'/api/cards/{mine["id"]}').status_code == 204


def test_card_de_cliente_de_fora_da_404(dev, others_card, loja):
    Membership.objects.filter(user=dev).delete()

    assert api_for(dev).get(f'/api/cards/{others_card.id}').status_code == 404


def test_comentario_de_outro_so_com_permissao(loja, dev, others_card, user):
    comment = Comment.objects.create(card=others_card, author=user, text='Da Ana')

    assert api_for(dev).delete(f'/api/comments/{comment.id}').status_code == 403
    manager = User.objects.create_user(email='ger@hubflow.com', password='x')
    manager.groups.add(Group.objects.get(name='Gerente'))
    assert api_for(manager).delete(f'/api/comments/{comment.id}').status_code == 204


def test_qualquer_membro_comenta_e_ve_o_card(loja, reader, others_card):
    api = api_for(reader)

    assert api.get(f'/api/cards/{others_card.id}').status_code == 200
    assert api.post(f'/api/cards/{others_card.id}/comments', {'text': 'Oi'}, **JSON).status_code == 201
