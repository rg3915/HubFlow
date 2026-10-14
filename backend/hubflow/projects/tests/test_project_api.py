import pytest

from hubflow.clients.models import Client
from hubflow.projects.models import Project

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme():
    return Client.objects.create(name='ACME', emails=['ti@acme.com'])


@pytest.fixture
def loja(acme):
    return Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')


def payload(acme, **overrides):
    data = {'client_id': acme.id, 'name': 'App', 'provider': 'gitlab', 'owner': 'acme', 'repo': 'app'}
    return data | overrides


def test_lista_projetos(api, loja):
    response = api.get('/api/projects')

    assert response.status_code == 200
    assert response.json() == [
        {
            'id': loja.id,
            'client_id': loja.client_id,
            'client_name': 'ACME',
            'name': 'Loja',
            'provider': 'github',
            'owner': 'acme',
            'repo': 'loja',
            'repository_url': 'https://github.com/acme/loja',
            'description': '',
            'emails': [],
            'is_active': True,
        }
    ]


def test_filtra_projetos_por_cliente(api, loja):
    beta = Client.objects.create(name='Beta')
    Project.objects.create(client=beta, name='Site', provider='github', owner='beta', repo='site')

    response = api.get(f'/api/projects?client={beta.id}')

    assert [p['name'] for p in response.json()] == ['Site']


def test_cria_projeto(api, acme):
    response = api.post('/api/projects', payload(acme, emails=['dev@acme.com']), content_type='application/json')

    assert response.status_code == 201
    project = Project.objects.get(name='App')
    assert (project.client, project.provider, project.emails) == (acme, 'gitlab', ['dev@acme.com'])
    assert response.json()['repository_url'] == 'https://gitlab.com/acme/app'


def test_cliente_inexistente_retorna_404(api, acme):
    response = api.post('/api/projects', payload(acme, client_id=999), content_type='application/json')

    assert response.status_code == 404


def test_provedor_invalido_retorna_422(api, acme):
    response = api.post('/api/projects', payload(acme, provider='bitbucket'), content_type='application/json')

    assert response.status_code == 422


def test_nome_repetido_no_cliente_retorna_400(api, acme, loja):
    # RN-21
    response = api.post('/api/projects', payload(acme, name='Loja', repo='outro'), content_type='application/json')

    assert response.status_code == 400
    assert 'nome' in response.json()['detail'].lower()


def test_repositorio_repetido_retorna_400(api, acme, loja):
    # RN-22
    data = payload(acme, provider='github', repo='loja')
    response = api.post('/api/projects', data, content_type='application/json')

    assert response.status_code == 400
    assert 'reposit' in response.json()['detail'].lower()


def test_detalhe_do_projeto(api, loja):
    response = api.get(f'/api/projects/{loja.id}')

    assert response.status_code == 200
    assert response.json()['name'] == 'Loja'


def test_edita_projeto(api, acme, loja):
    data = payload(acme, name='Loja Nova', provider='github', repo='loja', description='Loja virtual')

    response = api.put(f'/api/projects/{loja.id}', data, content_type='application/json')

    assert response.status_code == 200
    loja.refresh_from_db()
    assert (loja.name, loja.description) == ('Loja Nova', 'Loja virtual')


def test_exclui_projeto(api, loja):
    response = api.delete(f'/api/projects/{loja.id}')

    assert response.status_code == 204
    assert not Project.objects.filter(id=loja.id).exists()


def test_cliente_com_projetos_nao_pode_ser_excluido(api, acme, loja):
    # RN-11
    response = api.delete(f'/api/clients/{acme.id}')

    assert response.status_code == 400
    assert 'projeto' in response.json()['detail'].lower()
    assert Client.objects.filter(id=acme.id).exists()
