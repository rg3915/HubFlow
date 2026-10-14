import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.boards.models import Card, CustomField
from hubflow.permissions.models import Membership

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()


@pytest.fixture
def form(api, loja):
    """Formulário ligado; devolve o token público."""
    return api.put(f'/api/projects/{loja.id}/form', {'enabled': True}, **JSON).json()['token']


def public(**headers):
    return HttpClient(**headers)


def test_ligar_gera_token_e_caminho(api, loja):
    data = api.put(f'/api/projects/{loja.id}/form', {'enabled': True}, **JSON).json()

    assert data['enabled'] is True and len(data['token']) >= 20
    assert data['path'] == f'/form/{data["token"]}'
    assert api.get(f'/api/projects/{loja.id}/form').json() == data


def test_formulario_publico_mostra_projeto_e_campos(form, loja):
    CustomField.objects.create(project=loja, name='Prioridade', kind='select', options=['Alta'], required=True)

    data = public().get(f'/api/forms/{form}').json()

    assert data['project_name'] == 'Loja' and data['client_name'] == 'ACME'
    assert [(f['name'], f['required']) for f in data['fields']] == [('Prioridade', True)]


def test_envio_cria_card_no_backlog_sem_login(form, loja):
    field = CustomField.objects.create(project=loja, name='Prioridade', kind='select', options=['Alta'], required=True)
    body = {
        'title': 'Botão quebrado',
        'description': 'No checkout.',
        'email': 'cliente@acme.com',
        'fields': {str(field.id): 'Alta'},
    }

    response = public().post(f'/api/forms/{form}', body, **JSON)

    assert response.status_code == 201
    card = Card.objects.get()
    assert response.json() == {'number': card.number}
    assert (card.column, card.created_by, card.custom_values) == ('backlog', None, {str(field.id): 'Alta'})
    assert 'cliente@acme.com' in card.description and 'No checkout.' in card.description


def test_envio_valida_obrigatorios(form, loja):
    CustomField.objects.create(project=loja, name='Prioridade', kind='select', options=['Alta'], required=True)

    response = public().post(f'/api/forms/{form}', {'title': 'X'}, **JSON)

    assert response.status_code == 400 and 'Prioridade' in response.json()['detail']


def test_desligado_ou_token_antigo_da_404(api, loja, form):
    new = api.post(f'/api/projects/{loja.id}/form/regenerate').json()['token']

    assert new != form
    assert public().get(f'/api/forms/{form}').status_code == 404
    api.put(f'/api/projects/{loja.id}/form', {'enabled': False}, **JSON)
    assert public().get(f'/api/forms/{new}').status_code == 404


def test_limite_de_envios_por_ip(form, settings):
    settings.FORM_SUBMISSIONS_PER_HOUR = 2
    client = public(REMOTE_ADDR='10.0.0.7')

    codes = [client.post(f'/api/forms/{form}', {'title': f'Card {i}'}, **JSON).status_code for i in range(3)]

    assert codes == [201, 201, 429]
    assert public(REMOTE_ADDR='10.0.0.8').post(f'/api/forms/{form}', {'title': 'Outro IP'}, **JSON).status_code == 201


def test_so_quem_edita_o_projeto_configura(loja):
    dev = get_user_model().objects.create_user(email='dev@hubflow.com', password='x')
    dev.groups.add(Group.objects.get(name='Desenvolvedor'))
    Membership.objects.create(user=dev, client=loja.client)
    api = HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=dev).key}'})

    assert api.get(f'/api/projects/{loja.id}/form').status_code == 403
    assert api.put(f'/api/projects/{loja.id}/form', {'enabled': True}, **JSON).status_code == 403
