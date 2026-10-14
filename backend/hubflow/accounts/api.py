from urllib.parse import urlencode

import httpx
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponseRedirect
from ninja import File, Router, Schema, Status
from ninja.errors import HttpError
from ninja.files import UploadedFile

from hubflow.permissions.services import effective_permissions, require

from . import social
from .models import Token, User
from .schemas import ChangePasswordIn, DetailOut, ForgotPasswordIn, LoginIn, MeOut, ResetPasswordIn, TokenOut, UserOut
from .services import get_user_from_reset_link, send_password_reset_email

router = Router(tags=['auth'])


@router.post('/login', response=TokenOut, auth=None)
def login(request, data: LoginIn):
    user = authenticate(request, email=data.email, password=data.password)
    if user is None:
        raise HttpError(401, 'E-mail ou senha inválidos.')
    is_cli = request.headers.get('X-HubFlow-Client') == 'cli'
    if is_cli:
        require(user, 'permissions.use_cli')
    token = Token.objects.create(user=user, is_cli=is_cli)
    return {'token': token.key}


@router.get('/me', response=MeOut)
def me(request):
    user = request.user
    return {
        'id': user.id,
        'uuid': user.uuid,
        'email': user.email,
        'name': user.name,
        'first_name': user.first_name,
        'avatar_url': user.avatar.url if user.avatar else None,
        'is_superuser': user.is_superuser,
        'roles': sorted(user.groups.values_list('name', flat=True)),
        'permissions': sorted(effective_permissions(user)),
    }


AVATAR_MAX_BYTES = 2 * 1024 * 1024
AVATAR_TYPES = {'image/png', 'image/jpeg', 'image/webp'}


@router.post('/me/avatar', response={200: UserOut, 400: DetailOut})
def upload_avatar(request, file: UploadedFile = File(...)):
    if file.content_type not in AVATAR_TYPES:
        return Status(400, {'detail': 'Envie uma imagem PNG, JPG ou WebP.'})
    if file.size > AVATAR_MAX_BYTES:
        return Status(400, {'detail': 'Imagem grande demais. O tamanho máximo é 2 MB.'})
    user = request.user
    user.avatar.delete(save=False)  # substitui: o arquivo antigo não fica órfão
    user.avatar.save(file.name, file, save=True)
    return user


@router.delete('/me/avatar', response={204: None})
def delete_avatar(request):
    user = request.user
    user.avatar.delete(save=True)
    return Status(204, None)


@router.post('/logout', response={204: None})
def logout(request):
    # RN-05: revoga só o token usado nesta requisição.
    request.token.delete()
    return Status(204, None)


@router.post('/password/forgot', response=DetailOut, auth=None)
def password_forgot(request, data: ForgotPasswordIn):
    # RN-03: resposta igual exista ou não o e-mail.
    user = User.objects.filter(email=data.email.lower(), is_active=True).first()
    if user:
        send_password_reset_email(user)
    return {'detail': 'Se o e-mail estiver cadastrado, você receberá as instruções.'}


@router.post('/password/reset', response={200: DetailOut, 400: DetailOut}, auth=None)
def password_reset(request, data: ResetPasswordIn):
    user = get_user_from_reset_link(data.uid, data.token)
    if user is None:
        return Status(400, {'detail': 'Link inválido ou já utilizado.'})
    try:
        validate_password(data.password, user)
    except ValidationError as error:
        return Status(400, {'detail': ' '.join(error.messages)})
    user.set_password(data.password)
    user.save()
    return {'detail': 'Senha redefinida com sucesso.'}


@router.post('/password/change', response={200: DetailOut, 400: DetailOut})
def password_change(request, data: ChangePasswordIn):
    user = request.user
    if not user.check_password(data.current_password):
        return Status(400, {'detail': 'Senha atual incorreta.'})
    try:
        validate_password(data.new_password, user)
    except ValidationError as error:
        return Status(400, {'detail': ' '.join(error.messages)})
    user.set_password(data.new_password)
    user.save()
    return {'detail': 'Senha alterada com sucesso.'}


users_router = Router(tags=['users'])


@users_router.get('', response=list[UserOut])
def list_users(request):
    """Usuários ativos, para responsáveis e @menções."""
    return User.objects.filter(is_active=True).order_by('email')


class SocialCodeIn(Schema):
    code: str


def back_to_frontend(**query):
    return HttpResponseRedirect(f'{settings.FRONTEND_URL}/login/social?{urlencode(query)}')


class ProviderOut(Schema):
    id: str
    name: str


@router.get('/social/providers', response=list[ProviderOut], auth=None)
def social_providers(request):
    """Provedores com credenciais no .env (a tela de login mostra só estes botões)."""
    return [{'id': name, 'name': social.PROVIDERS[name]['name']} for name in social.configured()]


@router.get('/social/{provider}/start', auth=None)
def social_start(request, provider: str):
    if not social.credentials(provider):
        raise Http404('Provedor não configurado.')
    return HttpResponseRedirect(social.authorize_url(provider))


@router.get('/social/{provider}/callback', auth=None)
def social_callback(request, provider: str, code: str = '', state: str = '', error: str = ''):
    if error:  # a pessoa cancelou no provedor
        return back_to_frontend(error='access_denied')
    try:
        if not social.credentials(provider):
            raise social.SocialError('provider_error')
        social.check_state(provider, state)
        uid, email = social.identity(provider, social.access_token(provider, code))
        user = social.find_user(provider, uid, email)
    except social.SocialError as failure:
        return back_to_frontend(error=failure.code)
    except httpx.HTTPError:
        return back_to_frontend(error='provider_error')
    return back_to_frontend(code=social.login_code(user))


@router.post('/social/exchange', response={200: TokenOut, 400: DetailOut}, auth=None)
def social_exchange(request, data: SocialCodeIn):
    user = social.user_for_code(data.code)
    if user is None:
        return Status(400, {'detail': 'Código inválido ou expirado. Entre de novo.'})
    return {'token': Token.objects.create(user=user).key}
