import pytest
from django.apps import apps

from hubflow.boards.models import Card
from hubflow.clients.models import Client

pytestmark = pytest.mark.django_db

OWN_MODELS = [m for m in apps.get_models() if m.__module__.startswith('hubflow.') and m._meta.managed]


@pytest.mark.parametrize('model', OWN_MODELS, ids=lambda m: m.__name__)
def test_todo_model_tem_uuid_created_e_modified(model):
    fields = {f.name: f for f in model._meta.get_fields()}

    assert fields['uuid'].unique and not fields['uuid'].editable
    assert {'created', 'modified'} <= set(fields)


def test_uuid_e_versao_7_e_unico():
    first, second = Client.objects.create(name='A'), Client.objects.create(name='B')

    assert first.uuid.version == 7 and first.uuid != second.uuid


def test_api_expoe_uuid_alem_do_id(api, loja, user):
    card = Card.objects.create(project=loja, title='Login', created_by=user)

    assert api.get(f'/api/clients/{loja.client_id}').json()['uuid'] == str(loja.client.uuid)
    assert api.get(f'/api/projects/{loja.id}').json()['uuid'] == str(loja.uuid)
    data = api.get(f'/api/cards/{card.id}').json()
    assert data['id'] == card.id and data['uuid'] == str(card.uuid)
    assert data['created_by']['uuid'] == str(user.uuid)
    assert api.get('/api/auth/me').json()['uuid'] == str(user.uuid)
