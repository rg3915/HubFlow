from io import BytesIO
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


def image_bytes(format='PNG'):
    buffer = BytesIO()
    Image.new('RGB', (4, 4), 'blue').save(buffer, format=format)
    return buffer.getvalue()


def upload(api, name='foto.png', content=None, content_type='image/png'):
    file = SimpleUploadedFile(name, content if content is not None else image_bytes(), content_type=content_type)
    return api.post('/api/auth/me/avatar', {'file': file})


def test_me_sem_avatar_traz_url_nula_e_primeiro_nome(api, user):
    data = api.get('/api/auth/me').json()

    assert data == {'id': user.id, 'email': 'ana@example.com', 'name': 'Ana', 'avatar_url': None, 'first_name': 'Ana'}


def test_primeiro_nome_vem_do_email_quando_nao_ha_nome(api, user):
    user.name = ''
    user.save()

    assert api.get('/api/auth/me').json()['first_name'] == 'ana'


def test_primeiro_nome_e_a_primeira_palavra(api, user):
    user.name = 'Ana Maria Souza'
    user.save()

    assert api.get('/api/auth/me').json()['first_name'] == 'Ana'


def test_envia_avatar(api, user):
    response = upload(api)

    assert response.status_code == 200
    data = response.json()
    assert data['avatar_url'].startswith('/media/avatars/')
    user.refresh_from_db()
    assert user.avatar and Path(user.avatar.path).exists()
    assert api.get('/api/auth/me').json()['avatar_url'] == data['avatar_url']


def test_novo_avatar_apaga_o_anterior(api, user, tmp_path):
    upload(api, 'a.png')
    user.refresh_from_db()
    old_path = Path(user.avatar.path)

    upload(api, 'b.jpg', image_bytes('JPEG'), 'image/jpeg')

    user.refresh_from_db()
    assert not old_path.exists()
    assert Path(user.avatar.path).exists()


def test_avatar_grande_demais_retorna_400(api):
    response = upload(api, 'grande.png', image_bytes() + b'\0' * (2 * 1024 * 1024))

    assert response.status_code == 400
    assert '2 MB' in response.json()['detail']


def test_tipo_nao_suportado_retorna_400(api):
    response = upload(api, 'doc.pdf', b'%PDF', 'application/pdf')

    assert response.status_code == 400
    assert not api.get('/api/auth/me').json()['avatar_url']


def test_webp_e_aceito(api):
    assert upload(api, 'foto.webp', image_bytes('WEBP'), 'image/webp').status_code == 200


def test_remove_avatar(api, user):
    upload(api)
    user.refresh_from_db()
    path = Path(user.avatar.path)

    response = api.delete('/api/auth/me/avatar')

    assert response.status_code == 204
    assert not path.exists()
    assert api.get('/api/auth/me').json()['avatar_url'] is None


def test_remover_sem_avatar_nao_falha(api):
    assert api.delete('/api/auth/me/avatar').status_code == 204
