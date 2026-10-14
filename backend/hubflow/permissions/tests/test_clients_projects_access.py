import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.clients.models import Client
from hubflow.permissions.models import Membership
from hubflow.projects.models import Project

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
User = get_user_model()


def api_for(user):
    return HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=user).key}'})


@pytest.fixture
def world():
    acme, beta = Client.objects.create(name='ACME'), Client.objects.create(name='Beta')
    loja = Project.objects.create(client=acme, name='Loja', provider='github', owner='a', repo='l')
    site = Project.objects.create(client=beta, name='Site', provider='github', owner='b', repo='s')
    dev = User.objects.create_user(email='dev@hubflow.com', password='x')
    dev.groups.add(Group.objects.get(name='Desenvolvedor'))
    Membership.objects.create(user=dev, client=acme)
    return {'acme': acme, 'beta': beta, 'loja': loja, 'site': site, 'dev': dev, 'api': api_for(dev)}


def test_desenvolvedor_so_ve_os_clientes_de_que_e_membro(world):
    assert [c['name'] for c in world['api'].get('/api/clients').json()] == ['ACME']
    assert [p['name'] for p in world['api'].get('/api/projects').json()] == ['Loja']


def test_cliente_e_projeto_de_fora_dao_404(world):
    assert world['api'].get(f'/api/clients/{world["beta"].id}').status_code == 404
    assert world['api'].get(f'/api/projects/{world["site"].id}').status_code == 404
    assert world['api'].get(f'/api/projects/{world["site"].id}/board').status_code == 404


def test_gerente_ve_todos(world):
    manager = User.objects.create_user(email='ger@hubflow.com', password='x')
    manager.groups.add(Group.objects.get(name='Gerente'))

    assert len(api_for(manager).get('/api/clients').json()) == 2
    assert api_for(manager).get(f'/api/projects/{world["site"].id}/board').status_code == 200


def test_sem_permissao_nao_cria_nem_edita_nem_exclui_cliente(world):
    api = world['api']

    assert api.post('/api/clients', {'name': 'Novo'}, **JSON).status_code == 403
    assert api.put(f'/api/clients/{world["acme"].id}', {'name': 'X'}, **JSON).status_code == 403
    assert api.delete(f'/api/clients/{world["acme"].id}').status_code == 403


def test_sem_permissao_nao_cria_nem_edita_projeto(world):
    api = world['api']
    data = {'client_id': world['acme'].id, 'name': 'N', 'provider': 'github', 'owner': 'a', 'repo': 'n'}

    assert api.post('/api/projects', data, **JSON).status_code == 403
    assert api.put(f'/api/projects/{world["loja"].id}', data, **JSON).status_code == 403
    assert api.delete(f'/api/projects/{world["loja"].id}').status_code == 403
    assert api.post('/api/projects/full', data | {'client_name': 'Z'}, **JSON).status_code == 403


def test_mensagem_de_403_explica_a_permissao(world):
    response = world['api'].post('/api/clients', {'name': 'Novo'}, **JSON)

    assert 'Criar clientes' in response.json()['detail']


def test_gerente_cria_e_edita(world):
    manager = User.objects.create_user(email='ger@hubflow.com', password='x')
    manager.groups.add(Group.objects.get(name='Gerente'))

    assert api_for(manager).post('/api/clients', {'name': 'Novo'}, **JSON).status_code == 201


def test_superusuario_passa_por_tudo(world):
    admin = User.objects.create_superuser(email='admin@hubflow.com', password='x')

    gama = Client.objects.create(name='Gama')

    assert len(api_for(admin).get('/api/clients').json()) == 3
    assert api_for(admin).delete(f'/api/clients/{gama.id}').status_code == 204
