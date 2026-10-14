from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from hubflow.boards.models import Card
from hubflow.clients.models import Client
from hubflow.projects.models import Project
from hubflow.timetracking.models import TimeEntry

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


def test_cronometro_aberto_nao_tem_fim(card, ana):
    entry = TimeEntry.objects.create(card=card, user=ana, started_at=timezone.now())

    assert entry.ended_at is None
    assert entry.is_running is True
    assert entry.is_manual is False


def test_duracao_de_entrada_fechada(card, ana):
    start = timezone.now()
    entry = TimeEntry.objects.create(card=card, user=ana, started_at=start, ended_at=start + timedelta(minutes=90))

    assert entry.duration == timedelta(minutes=90)
    assert entry.hours == 1.5


def test_um_cronometro_aberto_por_card(card, ana):
    # RN-70
    TimeEntry.objects.create(card=card, user=ana, started_at=timezone.now())

    with pytest.raises(ValidationError):
        TimeEntry(card=card, user=ana, started_at=timezone.now()).full_clean()


def test_cronometros_abertos_em_cards_diferentes_sao_permitidos(loja, card, ana):
    # RN-70: sem --force, sem confirmação.
    other = Card.objects.create(project=loja, title='Outro')
    TimeEntry.objects.create(card=card, user=ana, started_at=timezone.now())

    TimeEntry(card=other, user=ana, started_at=timezone.now()).full_clean()


def test_fim_nao_pode_ser_antes_do_inicio(card, ana):
    now = timezone.now()

    with pytest.raises(ValidationError):
        TimeEntry(card=card, user=ana, started_at=now, ended_at=now - timedelta(minutes=1)).full_clean()


def test_entrada_manual_tem_duracao_e_data(card, ana):
    # RN-72
    entry = TimeEntry.objects.manual(card=card, user=ana, hours=1.5, date=timezone.localdate(), note='Reunião')

    assert entry.is_manual is True
    assert entry.duration == timedelta(hours=1.5)
    assert entry.started_at.date() == timezone.localdate()
    assert entry.note == 'Reunião'


def test_total_do_card_soma_so_as_fechadas(card, ana):
    start = timezone.now()
    TimeEntry.objects.create(card=card, user=ana, started_at=start, ended_at=start + timedelta(hours=1))
    TimeEntry.objects.manual(card=card, user=ana, hours=0.5, date=timezone.localdate())
    TimeEntry.objects.create(card=card, user=ana, started_at=start)  # aberta

    assert TimeEntry.objects.total_for(card) == timedelta(hours=1.5)


def test_cronometro_aberto_do_card(card, ana):
    running = TimeEntry.objects.create(card=card, user=ana, started_at=timezone.now())

    assert TimeEntry.objects.running_for(card) == running
