import pytest
from django.test import Client as HttpClient

from hubflow.clients.models import Client

pytestmark = pytest.mark.django_db


def test_lista_clientes_em_ordem_alfabetica(api):
    Client.objects.create(name='Zeta')
    Client.objects.create(name='Alfa', emails=['x@alfa.com'])

    response = api.get('/api/clients')

    assert response.status_code == 200
    data = response.json()
    assert [c['name'] for c in data] == ['Alfa', 'Zeta']
    assert data[0] == {'id': data[0]['id'], 'name': 'Alfa', 'emails': ['x@alfa.com'], 'is_active': True}


def test_cria_cliente(api):
    response = api.post('/api/clients', {'name': 'ACME', 'emails': ['ana@acme.com']}, content_type='application/json')

    assert response.status_code == 201
    assert response.json()['name'] == 'ACME'
    assert Client.objects.get(name='ACME').emails == ['ana@acme.com']


def test_cria_cliente_sem_emails(api):
    response = api.post('/api/clients', {'name': 'ACME'}, content_type='application/json')

    assert response.status_code == 201
    assert response.json()['emails'] == []


def test_nome_repetido_retorna_400(api):
    # RN-10
    Client.objects.create(name='ACME')

    response = api.post('/api/clients', {'name': 'ACME'}, content_type='application/json')

    assert response.status_code == 400
    assert 'nome' in response.json()['detail'].lower()


def test_email_invalido_retorna_422(api):
    response = api.post('/api/clients', {'name': 'ACME', 'emails': ['nao-e-email']}, content_type='application/json')

    assert response.status_code == 422


def test_detalhe_do_cliente(api):
    client = Client.objects.create(name='ACME')

    response = api.get(f'/api/clients/{client.id}')

    assert response.status_code == 200
    assert response.json()['name'] == 'ACME'


def test_cliente_inexistente_retorna_404(api):
    assert api.get('/api/clients/999').status_code == 404


def test_edita_cliente(api):
    client = Client.objects.create(name='ACME')

    response = api.put(
        f'/api/clients/{client.id}',
        {'name': 'ACME Corp', 'emails': ['ti@acme.com'], 'is_active': False},
        content_type='application/json',
    )

    assert response.status_code == 200
    client.refresh_from_db()
    assert (client.name, client.emails, client.is_active) == ('ACME Corp', ['ti@acme.com'], False)


def test_exclui_cliente_sem_projetos(api):
    client = Client.objects.create(name='ACME')

    response = api.delete(f'/api/clients/{client.id}')

    assert response.status_code == 204
    assert not Client.objects.filter(id=client.id).exists()


def test_exige_login():
    # RN-06
    assert HttpClient().get('/api/clients').status_code == 401
