"""Login com Google e GitHub (OAuth 2.0, authorization code) só para contas já cadastradas (RN-130)."""

import secrets
from urllib.parse import urlencode

import httpx
from django.conf import settings
from django.core.cache import cache

STATE_TTL = 600  # 10 min para voltar do provedor
CODE_TTL = 60  # código de uso único que o frontend troca pelo token

PROVIDERS = {
    'google': {
        'name': 'Google',
        'authorize': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token': 'https://oauth2.googleapis.com/token',
        'scope': 'openid email profile',
    },
    'github': {
        'name': 'GitHub',
        'authorize': 'https://github.com/login/oauth/authorize',
        'token': 'https://github.com/login/oauth/access_token',
        'scope': 'read:user user:email',
    },
}


class SocialError(Exception):
    """`code` vai na URL de volta ao frontend, que mostra a mensagem certa."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def credentials(provider):
    conf = settings.SOCIAL_PROVIDERS.get(provider) or {}
    return conf if provider in PROVIDERS and conf.get('client_id') and conf.get('secret') else None


def configured():
    return [name for name in PROVIDERS if credentials(name)]


def redirect_uri(provider):
    return f'{settings.BACKEND_URL}/api/auth/social/{provider}/callback'


def authorize_url(provider):
    # ponytail: state no cache padrão (memória do processo); com vários processos, usar Redis no CACHES.
    state = secrets.token_urlsafe(24)
    cache.set(f'oauth-state:{state}', provider, STATE_TTL)
    query = {
        'client_id': credentials(provider)['client_id'],
        'redirect_uri': redirect_uri(provider),
        'response_type': 'code',
        'scope': PROVIDERS[provider]['scope'],
        'state': state,
    }
    return f'{PROVIDERS[provider]["authorize"]}?{urlencode(query)}'


def check_state(provider, state):
    """State de uso único e do mesmo provedor (protege contra callback forjado)."""
    if not state or cache.get(f'oauth-state:{state}') != provider:
        raise SocialError('invalid_state')
    cache.delete(f'oauth-state:{state}')


def access_token(provider, code):
    conf = credentials(provider)
    data = {
        'client_id': conf['client_id'],
        'client_secret': conf['secret'],
        'code': code,
        'redirect_uri': redirect_uri(provider),
        'grant_type': 'authorization_code',
    }
    response = httpx.post(PROVIDERS[provider]['token'], data=data, headers={'Accept': 'application/json'}, timeout=10)
    token = response.json().get('access_token') if response.is_success else None
    if not token:
        raise SocialError('provider_error')
    return token


def identity(provider, token):
    """(uid, e-mail verificado ou None) da pessoa no provedor."""
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    if provider == 'google':
        info = httpx.get('https://openidconnect.googleapis.com/v1/userinfo', headers=headers, timeout=10).json()
        return str(info['sub']), info.get('email') if info.get('email_verified') else None
    user = httpx.get('https://api.github.com/user', headers=headers, timeout=10).json()
    emails = httpx.get('https://api.github.com/user/emails', headers=headers, timeout=10).json()
    primary = next((e['email'] for e in emails if e.get('primary') and e.get('verified')), None)
    return str(user['id']), primary


def find_user(provider, uid, email):
    """Conta já vinculada; senão, usuário ativo com o mesmo e-mail verificado (e vincula). Nunca cria usuário."""
    from .models import SocialAccount, User

    linked = SocialAccount.objects.select_related('user').filter(provider=provider, uid=uid).first()
    if linked:
        if not linked.user.is_active:
            raise SocialError('not_registered')
        return linked.user
    if not email:
        raise SocialError('email_not_verified')
    user = User.objects.filter(email=email.lower(), is_active=True).first()
    if user is None:
        raise SocialError('not_registered')
    SocialAccount.objects.create(user=user, provider=provider, uid=uid, email=email.lower())
    return user


def login_code(user):
    code = secrets.token_urlsafe(24)
    cache.set(f'oauth-login:{code}', user.id, CODE_TTL)
    return code


def user_for_code(code):
    from .models import User

    user_id = cache.get(f'oauth-login:{code}') if code else None
    cache.delete(f'oauth-login:{code}')
    return User.objects.filter(id=user_id, is_active=True).first() if user_id else None
