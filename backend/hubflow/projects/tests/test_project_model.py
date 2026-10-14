import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from hubflow.clients.models import Client
from hubflow.projects.models import Project

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme():
    return Client.objects.create(name='ACME')


def test_cria_projeto_do_github(acme):
    project = Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')

    assert project.client == acme  # RN-20
    assert project.repository_url == 'https://github.com/acme/loja'
    assert project.emails == []
    assert str(project) == 'ACME / Loja'


def test_url_do_gitlab(acme):
    project = Project.objects.create(client=acme, name='App', provider='gitlab', owner='acme', repo='app')

    assert project.repository_url == 'https://gitlab.com/acme/app'


def test_provedor_so_aceita_github_ou_gitlab(acme):
    # RN-22
    with pytest.raises(ValidationError):
        Project(client=acme, name='X', provider='bitbucket', owner='a', repo='b').full_clean()


def test_nome_e_unico_dentro_do_cliente(acme):
    # RN-21
    Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')

    with pytest.raises(IntegrityError):
        Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja2')


def test_mesmo_nome_em_clientes_diferentes_e_permitido(acme):
    other = Client.objects.create(name='Beta')
    Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')

    Project.objects.create(client=other, name='Loja', provider='github', owner='beta', repo='loja')

    assert Project.objects.filter(name='Loja').count() == 2


def test_repositorio_e_unico_no_sistema(acme):
    # RN-22: um repositório = um projeto.
    other = Client.objects.create(name='Beta')
    Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')

    with pytest.raises(IntegrityError):
        Project.objects.create(client=other, name='Outro', provider='github', owner='acme', repo='loja')


def test_owner_e_repo_sao_obrigatorios(acme):
    with pytest.raises(ValidationError):
        Project(client=acme, name='X', provider='github', owner='', repo='').full_clean()


def test_emails_de_notificacao_usam_os_do_cliente_quando_vazios(acme):
    # RN-23
    acme.emails = ['ti@acme.com']
    acme.save()
    project = Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')

    assert project.notification_emails == ['ti@acme.com']

    project.emails = ['dev@acme.com']
    assert project.notification_emails == ['dev@acme.com']


def test_cliente_nao_pode_ser_excluido_com_projetos(acme):
    # RN-11
    Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')

    with pytest.raises(IntegrityError):
        acme.delete()
