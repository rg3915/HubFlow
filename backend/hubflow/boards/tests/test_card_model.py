import pytest
from django.core.exceptions import ValidationError

from hubflow.boards.models import Card, Column
from hubflow.clients.models import Client
from hubflow.projects.models import Project

pytestmark = pytest.mark.django_db


@pytest.fixture
def loja():
    acme = Client.objects.create(name='ACME')
    return Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')


def test_colunas_fixas_na_ordem_do_fluxo():
    # RN-30
    assert [c.value for c in Column] == ['backlog', 'sprint', 'doing', 'qa', 'done', 'archived']
    assert Column.DOING.label == 'Em desenvolvimento'


def test_card_novo_entra_no_backlog_na_ultima_posicao(loja):
    # RN-31
    first = Card.objects.create(project=loja, title='Primeiro')
    second = Card.objects.create(project=loja, title='Segundo')

    assert (first.column, first.position) == (Column.BACKLOG, 0)
    assert (second.column, second.position) == (Column.BACKLOG, 1)


def test_numero_e_sequencial_por_projeto(loja):
    # RN-32
    other = Project.objects.create(client=loja.client, name='App', provider='github', owner='acme', repo='app')
    Card.objects.create(project=loja, title='A')
    Card.objects.create(project=loja, title='B')

    card = Card.objects.create(project=other, title='C')

    assert [c.number for c in loja.cards.order_by('number')] == [1, 2]
    assert card.number == 1


def test_numero_nao_e_reaproveitado_apos_exclusao(loja):
    # RN-32
    Card.objects.create(project=loja, title='A')
    Card.objects.create(project=loja, title='B').delete()

    assert Card.objects.create(project=loja, title='C').number == 3


def test_numero_e_unico_no_projeto(loja):
    Card.objects.create(project=loja, title='A')

    with pytest.raises(Exception):
        Card.objects.create(project=loja, title='B', number=1)


def test_titulo_e_obrigatorio(loja):
    # RN-38
    with pytest.raises(ValidationError):
        Card(project=loja, title='').full_clean()


def test_str_mostra_numero_e_titulo(loja):
    card = Card.objects.create(project=loja, title='Corrigir login')

    assert str(card) == '#1 Corrigir login'
