from django.contrib.auth import authenticate
from ninja import Router, Status
from ninja.errors import HttpError

from .models import Token, User
from .schemas import DetailOut, ForgotPasswordIn, LoginIn, TokenOut, UserOut
from .services import send_password_reset_email

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
