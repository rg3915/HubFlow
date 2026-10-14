import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.boards.models import Attachment
from hubflow.permissions.models import Membership

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


def upload(api, card, name='print.png', content=b'\x89PNG...', content_type='image/png'):
    file = SimpleUploadedFile(name, content, content_type=content_type)
    return api.post(f'/api/cards/{card.id}/attachments', {'file': file})


def test_envia_anexo(api, card, user):
    response = upload(api, card)

    assert response.status_code == 201
    data = response.json()
    assert data['name'] == 'print.png'
    assert data['size'] == len(b'\x89PNG...')
    assert data['uploaded_by']['email'] == 'ana@example.com'
    assert data['url'].startswith('/media/')
    assert Attachment.objects.get(id=data['id']).card == card


def test_lista_anexos(api, card):
    upload(api, card, 'a.txt', b'a', 'text/plain')
    upload(api, card, 'b.txt', b'b', 'text/plain')

    response = api.get(f'/api/cards/{card.id}/attachments')

    assert [a['name'] for a in response.json()] == ['a.txt', 'b.txt']


def test_arquivo_grande_demais_retorna_400(api, card, settings):
    settings.ATTACHMENT_MAX_BYTES = 10

    response = upload(api, card, 'grande.bin', b'x' * 11, 'application/octet-stream')

    assert response.status_code == 400
    assert 'MB' in response.json()['detail'] or 'tamanho' in response.json()['detail'].lower()


def test_sem_arquivo_retorna_422(api, card):
    assert api.post(f'/api/cards/{card.id}/attachments', {}).status_code == 422


def test_quem_enviou_exclui(api, card):
    attachment_id = upload(api, card).json()['id']

    response = api.delete(f'/api/attachments/{attachment_id}')

    assert response.status_code == 204
    assert not Attachment.objects.filter(id=attachment_id).exists()


def test_outro_usuario_nao_exclui(api, card):
    attachment_id = upload(api, card).json()['id']
    other = get_user_model().objects.create_user(email='bob@hubflow.com', password='segredo123')
    other.groups.add(Group.objects.get(name='Desenvolvedor'))  # vê o card, mas não é dono nem tem change_card
    Membership.objects.create(user=other, client=card.project.client)
    other_api = HttpClient(headers={'Authorization': f'Bearer {Token.objects.create(user=other).key}'})

    assert other_api.delete(f'/api/attachments/{attachment_id}').status_code == 403


def test_card_traz_quantidade_de_anexos(api, loja, card):
    upload(api, card)

    assert api.get(f'/api/cards/{card.id}').json()['attachments_count'] == 1
    assert api.get(f'/api/projects/{loja.id}/board').json()['columns'][0]['cards'][0]['attachments_count'] == 1
