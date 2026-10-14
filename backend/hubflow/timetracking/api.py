from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.accounts.schemas import DetailOut
from hubflow.boards.models import Card

from .models import TimeEntry
from .schemas import CardTimeOut, TimeEntryOut
from .services import start_timer, stop_timer

router = Router(tags=['time'])


@router.post('/cards/{card_id}/timer/start', response={201: TimeEntryOut, 400: DetailOut})
def timer_start(request, card_id: int):
    card = get_object_or_404(Card, id=card_id)
    try:
        return Status(201, start_timer(card, request.user))
    except ValidationError as error:
        return Status(400, {'detail': ' '.join(error.messages)})


@router.post('/cards/{card_id}/timer/stop', response={200: TimeEntryOut, 400: DetailOut})
def timer_stop(request, card_id: int):
    entry = stop_timer(get_object_or_404(Card, id=card_id))
    if entry is None:
        return Status(400, {'detail': 'Este card não tem cronômetro aberto.'})
    return entry


@router.get('/cards/{card_id}/time', response=CardTimeOut)
def card_time(request, card_id: int):
    card = get_object_or_404(Card, id=card_id)
    entries = list(card.time_entries.select_related('user'))
    return {
        'entries': entries,
        'total_hours': round(TimeEntry.objects.total_for(card).total_seconds() / 3600, 2),
        'running': next((e for e in entries if e.is_running), None),
    }
