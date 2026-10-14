from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from ninja import Router, Status
from ninja.errors import HttpError

from .models import Token, User
from .schemas import ChangePasswordIn, DetailOut, ForgotPasswordIn, LoginIn, ResetPasswordIn, TokenOut, UserOut
from .services import get_user_from_reset_link, send_password_reset_email

router = Router(tags=['auth'])


@router.post('/login', response=TokenOut, auth=None)
def login(request, data: LoginIn):
    user = authenticate(request, email=data.email, password=data.password)
    if user is None:
        raise HttpError(401, 'E-mail ou senha inválidos.')
    token = Token.objects.create(user=user)
    return {'token': token.key}


@router.get('/me', response=UserOut)
def me(request):
    return request.user


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
