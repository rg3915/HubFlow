from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from hubflow.boards.models import Card
from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.timetracking.models import TimeEntry
from hubflow.timetracking.services import start_timer, stop_timer

pytestmark = pytest.mark.django_db


@pytest.fixture
def loja():
    acme = Client.objects.create(name='ACME')
    return Project.objects.create(client=acme, name='Loja', provider='github', owner='acme', repo='loja')


@pytest.fixture
def card(loja):
    return Card.objects.create(project=loja, title='Corrigir login')


@pytest.fixture
def ana(db):
    return get_user_model().objects.create_user(email='ana@hubflow.com', password='segredo123')


def closed_entry(card, user, ended_minutes_ago):
    end = timezone.now() - timedelta(minutes=ended_minutes_ago)
    return TimeEntry.objects.create(card=card, user=user, started_at=end - timedelta(hours=1), ended_at=end)


def test_inicia_cronometro_agora(card, ana):
    entry = start_timer(card, ana)

    assert entry.is_running
    assert abs((timezone.now() - entry.started_at).total_seconds()) < 5


def test_regra_dos_15_minutos_continua_do_fim_anterior(loja, card, ana):
    # RN-71: parou há menos de 15 min no mesmo projeto → começa onde parou.
    other = Card.objects.create(project=loja, title='Outro')
    previous = closed_entry(other, ana, ended_minutes_ago=10)

    entry = start_timer(card, ana)

    assert entry.started_at == previous.ended_at


def test_mais_de_15_minutos_comeca_agora(card, ana):
    closed_entry(card, ana, ended_minutes_ago=20)

    entry = start_timer(card, ana)

    assert abs((timezone.now() - entry.started_at).total_seconds()) < 5


def test_projeto_diferente_nao_continua(loja, card, ana):
    other_project = Project.objects.create(client=loja.client, name='App', provider='github', owner='acme', repo='app')
    other_card = Card.objects.create(project=other_project, title='X')
    closed_entry(other_card, ana, ended_minutes_ago=5)

    entry = start_timer(card, ana)

    assert abs((timezone.now() - entry.started_at).total_seconds()) < 5


def test_outro_usuario_nao_continua(loja, card, ana):
    bob = get_user_model().objects.create_user(email='bob@hubflow.com', password='segredo123')
    closed_entry(card, bob, ended_minutes_ago=5)

    entry = start_timer(card, ana)

    assert abs((timezone.now() - entry.started_at).total_seconds()) < 5


def test_segundo_cronometro_no_mesmo_card_e_recusado(card, ana):
    # RN-70
    start_timer(card, ana)

    with pytest.raises(ValidationError):
        start_timer(card, ana)


def test_para_o_cronometro(card, ana):
    start_timer(card, ana)

    entry = stop_timer(card)

    assert entry.ended_at is not None
    assert TimeEntry.objects.running_for(card) is None


def test_parar_sem_cronometro_aberto_retorna_none(card):
    assert stop_timer(card) is None


def test_lancamento_manual_nao_puxa_a_continuidade(card, ana):
    # RN-71 vale só para cronômetros: um lançamento manual (09:00–09:30 de hoje) não é "parou há pouco".
    TimeEntry.objects.manual(card=card, user=ana, hours=0.5, date=timezone.localdate())

    entry = start_timer(card, ana)

    assert abs((timezone.now() - entry.started_at).total_seconds()) < 5


def test_entrada_que_termina_no_futuro_nao_puxa_a_continuidade(card, ana):
    future_end = timezone.now() + timedelta(hours=2)
    TimeEntry.objects.create(card=card, user=ana, started_at=future_end - timedelta(hours=1), ended_at=future_end)

    entry = start_timer(card, ana)

    assert abs((timezone.now() - entry.started_at).total_seconds()) < 5
