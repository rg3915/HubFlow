import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.boards.models import CustomField
from hubflow.permissions.models import Membership

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


def add(api, loja, **data):
    return api.post(f'/api/projects/{loja.id}/fields', {'name': 'Prioridade', 'kind': 'text'} | data, **JSON)


def test_cria_e_lista(api, loja):
    response = add(api, loja, kind='select', options=['Alta', 'Baixa'], required=True)

    assert response.status_code == 201
    field = CustomField.objects.get()
    assert response.json() == {
        'id': field.id,
        'uuid': str(field.uuid),
        'project_id': loja.id,
        'name': 'Prioridade',
        'kind': 'select',
        'options': ['Alta', 'Baixa'],
        'required': True,
        'position': 0,
    }
    assert [f['name'] for f in api.get(f'/api/projects/{loja.id}/fields').json()] == ['Prioridade']


def test_validacoes_retornam_400(api, loja):
    add(api, loja)

    assert 'Já existe' in add(api, loja, name='prioridade').json()['detail']
    assert 'opção' in add(api, loja, name='Status', kind='select').json()['detail']


def test_edita_e_exclui(api, loja):
    field_id = add(api, loja).json()['id']

    edited = api.put(f'/api/fields/{field_id}', {'name': 'Urgência', 'kind': 'bool'}, **JSON)
    assert edited.status_code == 200 and edited.json()['kind'] == 'bool'
    assert api.delete(f'/api/fields/{field_id}').status_code == 204
    assert not CustomField.objects.exists()


def test_reordena(api, loja):
    a, b, c = (add(api, loja, name=name).json()['id'] for name in ('A', 'B', 'C'))

    response = api.put(f'/api/projects/{loja.id}/fields/order', {'ids': [c, a, b]}, **JSON)

    assert [f['name'] for f in response.json()] == ['C', 'A', 'B']


def test_sem_permissao_so_lista(loja):
    dev = get_user_model().objects.create_user(email='dev@hubflow.com', password='x')
    dev.groups.add(Group.objects.get(name='Desenvolvedor'))
    Membership.objects.create(user=dev, client=loja.client)
    api = HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=dev).key}'})
    field = CustomField.objects.create(project=loja, name='Prioridade', kind='text')

    assert api.get(f'/api/projects/{loja.id}/fields').status_code == 200
    assert add(api, loja, name='Outro').status_code == 403
    assert api.put(f'/api/fields/{field.id}', {'name': 'X', 'kind': 'text'}, **JSON).status_code == 403
    assert api.delete(f'/api/fields/{field.id}').status_code == 403
    assert api.put(f'/api/projects/{loja.id}/fields/order', {'ids': [field.id]}, **JSON).status_code == 403
