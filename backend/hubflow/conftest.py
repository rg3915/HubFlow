import pytest
from django.contrib.auth import get_user_model
from django.test import Client as HttpClient

from hubflow.accounts.models import Token


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(email='ana@example.com', password='segredo123', name='Ana')


@pytest.fixture
def api(user):
    """Cliente HTTP já autenticado com um token do usuário."""
    token = Token.objects.create(user=user)
    return HttpClient(headers={'Authorization': f'Bearer {token.key}'})
