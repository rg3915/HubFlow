from datetime import date

import pytest
from django.core.exceptions import ValidationError

from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.sprints.models import Sprint

pytestmark = pytest.mark.django_db


@pytest.fixture
def loja():
    acme = Client.objects.create(name='ACME')
    return Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')


def test_numero_sequencial_por_projeto(loja):
    # RN-60
    other = Project.objects.create(client=loja.client, name='App', provider='github', owner='acme', repo='app')
    first = Sprint.objects.create(project=loja)
    second = Sprint.objects.create(project=loja)

    assert (first.number, second.number) == (1, 2)
    assert Sprint.objects.create(project=other).number == 1


def test_numero_nao_e_reaproveitado(loja):
    Sprint.objects.create(project=loja)
    Sprint.objects.create(project=loja).delete()

    assert Sprint.objects.create(project=loja).number == 3


def test_nome_datas_e_milestone_sao_opcionais(loja):
    sprint = Sprint.objects.create(project=loja)

    assert (sprint.name, sprint.start_date, sprint.end_date, sprint.milestone) == ('', None, None, None)
    assert sprint.is_open is True
    assert str(sprint) == 'Sprint 1'


def test_nome_entra_na_descricao(loja):
    sprint = Sprint.objects.create(project=loja, name='Checkout')

    assert str(sprint) == 'Sprint 1 · Checkout'


def test_fim_nao_pode_ser_antes_do_inicio(loja):
    sprint = Sprint(project=loja, start_date=date(2026, 10, 20), end_date=date(2026, 10, 10))

    with pytest.raises(ValidationError):
        sprint.full_clean()


def test_fechar_sprint(loja):
    sprint = Sprint.objects.create(project=loja)

    sprint.close()

    sprint.refresh_from_db()
    assert sprint.is_open is False
    assert sprint.closed_at is not None


def test_sprint_aberta_mais_recente_do_projeto(loja):
    Sprint.objects.create(project=loja).close()
    second = Sprint.objects.create(project=loja)
    Sprint.objects.create(project=loja).close()

    assert Sprint.objects.latest_open(loja) == second


def test_sem_sprint_aberta_devolve_none(loja):
    assert Sprint.objects.latest_open(loja) is None
