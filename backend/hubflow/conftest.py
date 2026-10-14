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


@pytest.fixture
def loja(db):
    from hubflow.clients.models import Client
    from hubflow.projects.models import Project

    acme = Client.objects.create(name='ACME')
    return Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')


@pytest.fixture
def card(loja):
    from hubflow.boards.models import Card

    return Card.objects.create(project=loja, title='Corrigir login')
