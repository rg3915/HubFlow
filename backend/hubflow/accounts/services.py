from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


def send_password_reset_email(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f'{settings.FRONTEND_URL}/reset-password/{uid}/{token}'
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
