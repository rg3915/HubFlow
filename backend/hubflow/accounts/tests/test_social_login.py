from urllib.parse import parse_qs, urlparse

import pytest
import respx
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client
from httpx import Response

from hubflow.accounts.models import SocialAccount, Token

pytestmark = pytest.mark.django_db
JSON = {'content_type': 'application/json'}


@pytest.fixture(autouse=True)
def oauth(settings):
    cache.clear()
    settings.BACKEND_URL = 'http://api.test'
    settings.FRONTEND_URL = 'http://app.test'
    settings.SOCIAL_PROVIDERS = {
        'google': {'client_id': 'g-id', 'secret': 'g-secret'},
        'github': {'client_id': 'gh-id', 'secret': 'gh-secret'},
    }


def start(provider):
    response = Client().get(f'/api/auth/social/{provider}/start')
    assert response.status_code == 302
    url = urlparse(response['Location'])
    return url, parse_qs(url.query)


def callback(provider, state, code='abc'):
    response = Client().get(f'/api/auth/social/{provider}/callback', {'code': code, 'state': state})
    assert response.status_code == 302
    return urlparse(response['Location'])


def mock_google(email='ana@example.com', verified=True, sub='g-123'):
    respx.post('https://oauth2.googleapis.com/token').mock(return_value=Response(200, json={'access_token': 'tok'}))
    userinfo = {'sub': sub, 'email': email, 'email_verified': verified, 'name': 'Ana'}
    respx.get('https://openidconnect.googleapis.com/v1/userinfo').mock(return_value=Response(200, json=userinfo))


def exchange(code):
    return Client().post('/api/auth/social/exchange', {'code': code}, **JSON)


def test_inicio_redireciona_ao_google_com_state():
    url, query = start('google')

    assert url.netloc == 'accounts.google.com'
    assert query['client_id'] == ['g-id'] and query['response_type'] == ['code']
    assert query['redirect_uri'] == ['http://api.test/api/auth/social/google/callback']
    assert 'email' in query['scope'][0] and query['state'][0]


@respx.mock
def test_google_entra_na_conta_cadastrada_pelo_email(user):
    _, query = start('google')
    mock_google()

    back = callback('google', query['state'][0])

    assert f'{back.scheme}://{back.netloc}{back.path}' == 'http://app.test/login/social'
    code = parse_qs(back.query)['code'][0]
    token = exchange(code).json()['token']
    assert Token.objects.get(key=token).user == user
    assert SocialAccount.objects.get().uid == 'g-123'
    assert exchange(code).status_code == 400  # código de uso único


@respx.mock
def test_github_usa_o_email_principal_verificado(user):
    _, query = start('github')
    respx.post('https://github.com/login/oauth/access_token').mock(
        return_value=Response(200, json={'access_token': 't'})
    )
    respx.get('https://api.github.com/user').mock(
        return_value=Response(200, json={'id': 42, 'login': 'ana', 'name': 'Ana'})
    )
    emails = [
        {'email': 'outro@example.com', 'primary': False, 'verified': True},
        {'email': 'ANA@example.com', 'primary': True, 'verified': True},
    ]
    respx.get('https://api.github.com/user/emails').mock(return_value=Response(200, json=emails))

    code = parse_qs(callback('github', query['state'][0]).query)['code'][0]

    assert Token.objects.get(key=exchange(code).json()['token']).user == user
    assert SocialAccount.objects.get(provider='github').uid == '42'


@respx.mock
def test_email_nao_cadastrado_nao_cria_conta(db):
    _, query = start('google')
    mock_google(email='estranho@example.com')

    back = callback('google', query['state'][0])

    assert parse_qs(back.query)['error'] == ['not_registered']
    assert not get_user_model().objects.exists()


@respx.mock
def test_email_nao_verificado_e_recusado(user):
    _, query = start('google')
    mock_google(verified=False)

    assert parse_qs(callback('google', query['state'][0]).query)['error'] == ['email_not_verified']


def test_state_invalido_ou_reusado(user):
    assert parse_qs(callback('google', 'forjado').query)['error'] == ['invalid_state']


@respx.mock
def test_conta_ja_vinculada_entra_mesmo_se_o_email_mudou(user):
    SocialAccount.objects.create(user=user, provider='google', uid='g-123')
    _, query = start('google')
    mock_google(email='novo-email@example.com')

    code = parse_qs(callback('google', query['state'][0]).query)['code'][0]

    assert Token.objects.get(key=exchange(code).json()['token']).user == user


def test_usuario_desativado_nao_entra(user):
    user.is_active = False
    user.save()
    SocialAccount.objects.create(user=user, provider='google', uid='g-123')

    with respx.mock:
        _, query = start('google')
        mock_google()
        back = callback('google', query['state'][0])

    assert parse_qs(back.query)['error'] == ['not_registered']


def test_provedor_nao_configurado_da_404(settings):
    settings.SOCIAL_PROVIDERS = {'google': {'client_id': '', 'secret': ''}}

    assert Client().get('/api/auth/social/google/start').status_code == 404
    assert Client().get('/api/auth/social/facebook/start').status_code == 404


def test_cancelado_no_provedor():
    back = urlparse(Client().get('/api/auth/social/google/callback', {'error': 'access_denied'})['Location'])

    assert parse_qs(back.query)['error'] == ['access_denied']


def test_lista_publica_dos_provedores_configurados(settings):
    settings.SOCIAL_PROVIDERS['github'] = {'client_id': '', 'secret': ''}

    assert Client().get('/api/auth/social/providers').json() == [{'id': 'google', 'name': 'Google'}]
