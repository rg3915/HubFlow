import pytest
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError

User = get_user_model()

pytestmark = pytest.mark.django_db


def test_usuario_e_identificado_pelo_email():
    user = User.objects.create_user(email='ana@example.com', password='segredo123')

    assert user.email == 'ana@example.com'
    assert user.check_password('segredo123')
    assert User.USERNAME_FIELD == 'email'
    assert not hasattr(user, 'username')


def test_email_e_guardado_em_minusculas():
    user = User.objects.create_user(email='Ana@Example.COM', password='segredo123')

    assert user.email == 'ana@example.com'


def test_email_e_unico_sem_diferenciar_maiusculas():
    User.objects.create_user(email='ana@example.com', password='segredo123')

    with pytest.raises(IntegrityError):
        User.objects.create_user(email='ANA@example.com', password='outra1234')


def test_login_aceita_email_em_qualquer_caixa():
    User.objects.create_user(email='ana@example.com', password='segredo123')

    assert authenticate(email='ANA@EXAMPLE.COM', password='segredo123') is not None


def test_email_e_obrigatorio():
    with pytest.raises(ValueError):
        User.objects.create_user(email='', password='segredo123')


def test_superusuario_por_email():
    admin = User.objects.create_superuser(email='admin@example.com', password='segredo123')

    assert admin.is_staff
    assert admin.is_superuser
