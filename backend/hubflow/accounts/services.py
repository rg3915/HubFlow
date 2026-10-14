from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


def password_link(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    return f'{settings.FRONTEND_URL}/reset-password/{uid}/{default_token_generator.make_token(user)}'


def send_invite_email(user, invited_by):
    body = (
        f'Olá{", " + user.first_name if user.first_name else ""},\n\n'
        f'{invited_by.name or invited_by.email} convidou você para o HubFlow.\n'
        f'Para definir sua senha e entrar, acesse:\n\n{password_link(user)}\n\n'
        f'Seu login é o e-mail {user.email}. O link vale por 24 horas.\n'
    )
    EmailMessage(subject='Convite para o HubFlow', body=body, to=[user.email]).send()


def send_password_reset_email(user):
    link = password_link(user)
    body = (
        'Olá,\n\n'
        'Recebemos um pedido para redefinir a senha da sua conta no HubFlow.\n'
        f'Para escolher uma nova senha, acesse:\n\n{link}\n\n'
        'O link vale por 24 horas. Se não foi você, ignore este e-mail.\n'
    )
    EmailMessage(subject='Redefinição de senha - HubFlow', body=body, to=[user.email]).send()


def get_user_from_reset_link(uid, token):
    """Devolve o usuário do link de redefinição ou None se uid/token forem inválidos ou já usados."""
    from .models import User

    try:
        user = User.objects.get(pk=urlsafe_base64_decode(uid).decode())
    except ValueError, OverflowError, User.DoesNotExist:
        return None
    if not default_token_generator.check_token(user, token):
        return None
    return user
