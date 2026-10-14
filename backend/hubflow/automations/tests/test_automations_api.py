import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.automations.models import Automation
from hubflow.permissions.models import Membership

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
MOVE = {
    'name': 'QA aprovado',
    'trigger': 'entered_column',
    'trigger_column': 'qa',
    'action': 'move',
    'action_column': 'done',
}


def test_cria_lista_e_descreve(api, loja, user):
    response = api.post(f'/api/projects/{loja.id}/automations', MOVE, **JSON)

    assert response.status_code == 201
    rule = Automation.objects.get()
    assert rule.created_by == user
    data = api.get(f'/api/projects/{loja.id}/automations').json()
    assert data == [
        {
            'id': rule.id,
            'uuid': str(rule.uuid),
            'project_id': loja.id,
            'name': 'QA aprovado',
            'is_active': True,
            'trigger': 'entered_column',
            'trigger_column': 'qa',
            'action': 'move',
            'action_column': 'done',
            'action_user_id': None,
            'action_label_id': None,
            'description': 'Quando o card entrar em QA → mover para Concluído',
        }
    ]


def test_invalida_retorna_400(api, loja):
    response = api.post(f'/api/projects/{loja.id}/automations', MOVE | {'action_column': ''}, **JSON)

    assert response.status_code == 400 and 'coluna de destino' in response.json()['detail']


def test_responsavel_precisa_existir(api, loja):
    body = {'name': 'X', 'trigger': 'created', 'action': 'assign', 'action_user_id': 999999}

    assert api.post(f'/api/projects/{loja.id}/automations', body, **JSON).status_code == 400


def test_edita_desliga_e_exclui(api, loja):
    rule_id = api.post(f'/api/projects/{loja.id}/automations', MOVE, **JSON).json()['id']

    edited = api.put(f'/api/automations/{rule_id}', MOVE | {'name': 'Novo', 'is_active': False}, **JSON).json()
    assert edited['name'] == 'Novo' and edited['is_active'] is False
    assert api.delete(f'/api/automations/{rule_id}').status_code == 204
    assert not Automation.objects.exists()


def test_sem_permissao_so_lista(loja):
    dev = get_user_model().objects.create_user(email='dev@hubflow.com', password='x')
    dev.groups.add(Group.objects.get(name='Desenvolvedor'))
    Membership.objects.create(user=dev, client=loja.client)
    api = HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=dev).key}'})
    rule = Automation.objects.create(project=loja, name='R', trigger='created', action='notify')

    assert api.get(f'/api/projects/{loja.id}/automations').status_code == 200
    assert api.post(f'/api/projects/{loja.id}/automations', MOVE, **JSON).status_code == 403
    assert api.put(f'/api/automations/{rule.id}', MOVE, **JSON).status_code == 403
    assert api.delete(f'/api/automations/{rule.id}').status_code == 403
