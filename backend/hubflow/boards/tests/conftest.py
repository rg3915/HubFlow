import pytest

from hubflow.boards.models import Card
from hubflow.clients.models import Client
from hubflow.projects.models import Project


@pytest.fixture
def loja(db):
    acme = Client.objects.create(name='ACME')
    return Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')


@pytest.fixture
def card(loja):
    return Card.objects.create(project=loja, title='Corrigir login')
