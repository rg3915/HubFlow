import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.boards.models import Attachment, Card, Label
from hubflow.permissions.models import Membership
from hubflow.sprints.models import Sprint

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}
User = get_user_model()


@pytest.fixture(autouse=True)
def media_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


def api_for(user):
    return HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=user).key}'})


def member(loja, role, email):
    person = User.objects.create_user(email=email, password='x', name=email.split('@')[0])
    person.groups.add(Group.objects.get(name=role))
    Membership.objects.create(user=person, client=loja.client)
    return person


def test_leitura_nao_mexe_em_sprints(loja):
    api = api_for(member(loja, 'Leitura', 'leitura@hubflow.com'))
    sprint = Sprint.objects.create(project=loja)

    assert api.get(f'/api/projects/{loja.id}/sprints').status_code == 200
    assert api.post(f'/api/projects/{loja.id}/sprints', {}, **JSON).status_code == 403
    assert api.put(f'/api/sprints/{sprint.id}', {'name': 'x'}, **JSON).status_code == 403
    assert api.post(f'/api/sprints/{sprint.id}/close').status_code == 403
    assert api.delete(f'/api/sprints/{sprint.id}').status_code == 403
    assert api.post(f'/api/projects/{loja.id}/milestones', {'title': 'v1'}, **JSON).status_code == 403


def test_gerente_gerencia_sprints(loja):
    api = api_for(member(loja, 'Gerente', 'ger@hubflow.com'))

    assert api.post(f'/api/projects/{loja.id}/sprints', {}, **JSON).status_code == 201


def test_desenvolvedor_gerencia_etiquetas_leitura_nao(loja):
    dev_api = api_for(member(loja, 'Desenvolvedor', 'dev@hubflow.com'))
    reader_api = api_for(member(loja, 'Leitura', 'leitura@hubflow.com'))

    created = dev_api.post(f'/api/projects/{loja.id}/labels', {'name': 'bug', 'color': '#a33a2e'}, **JSON)
    assert created.status_code == 201
    assert reader_api.get(f'/api/projects/{loja.id}/labels').status_code == 200
    label_in = {'name': 'ui', 'color': '#000000'}
    assert reader_api.post(f'/api/projects/{loja.id}/labels', label_in, **JSON).status_code == 403
    label_id = created.json()['id']
    assert reader_api.put(f'/api/labels/{label_id}', label_in, **JSON).status_code == 403
    assert reader_api.delete(f'/api/labels/{label_id}').status_code == 403
    assert dev_api.delete(f'/api/labels/{label_id}').status_code == 204


def test_sprint_e_etiqueta_de_cliente_de_fora_dao_404(loja):
    outsider = User.objects.create_user(email='fora@hubflow.com', password='x')
    outsider.groups.add(Group.objects.get(name='Desenvolvedor'))  # sem vínculo com o cliente
    api = api_for(outsider)
    sprint = Sprint.objects.create(project=loja)
    label = Label.objects.create(project=loja, name='bug')

    assert api.get(f'/api/projects/{loja.id}/sprints').status_code == 404
    assert api.put(f'/api/sprints/{sprint.id}', {'name': 'x'}, **JSON).status_code == 404
    assert api.get(f'/api/projects/{loja.id}/labels').status_code == 404
    assert api.delete(f'/api/labels/{label.id}').status_code == 404


def test_anexo_segue_a_regra_do_card(loja, user):
    dev = member(loja, 'Desenvolvedor', 'dev@hubflow.com')
    api = api_for(dev)
    others_card = Card.objects.create(project=loja, title='Da Ana', created_by=user)
    mine = Card.objects.create(project=loja, title='Meu', created_by=dev)

    assert (
        api.post(f'/api/cards/{others_card.id}/attachments', {'file': SimpleUploadedFile('a.txt', b'a')}).status_code
        == 403
    )
    assert (
        api.post(f'/api/cards/{mine.id}/attachments', {'file': SimpleUploadedFile('a.txt', b'a')}).status_code == 201
    )
    attachment = Attachment.objects.create(card=others_card, name='x', size=1, uploaded_by=user, file='x.txt')
    assert api.delete(f'/api/attachments/{attachment.id}').status_code == 403
