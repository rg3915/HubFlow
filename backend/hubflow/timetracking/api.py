from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from ninja import Router, Status
from ninja.errors import HttpError

from hubflow.accounts.schemas import DetailOut
from hubflow.boards.models import Card

from .models import TimeEntry
from .schemas import CardTimeOut, ManualEntryIn, TimeEntryOut
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


def own_entry_or_403(request, entry_id):
    # RN-73: só o dono mexe na própria entrada (cronômetro ou manual).
    entry = get_object_or_404(TimeEntry.objects.select_related('user'), id=entry_id)
    if entry.user_id != request.user.id:
        raise HttpError(403, 'Só quem registrou este tempo pode alterá-lo.')
    return entry


@router.post('/cards/{card_id}/time-entries', response={201: TimeEntryOut})
def add_manual_entry(request, card_id: int, data: ManualEntryIn):
    card = get_object_or_404(Card, id=card_id)
    return Status(201, TimeEntry.objects.manual(card, request.user, data.hours, data.date, data.note))


@router.put('/time-entries/{entry_id}', response={200: TimeEntryOut, 400: DetailOut})
def update_manual_entry(request, entry_id: int, data: ManualEntryIn):
    entry = own_entry_or_403(request, entry_id)
    if entry.is_running:
        return Status(400, {'detail': 'Pare o cronômetro antes de editar.'})
    entry.started_at, entry.ended_at = TimeEntry.objects.manual_span(data.hours, data.date)
    entry.note, entry.is_manual = data.note, True
    entry.save(update_fields=['started_at', 'ended_at', 'note', 'is_manual'])
    return entry


@router.delete('/time-entries/{entry_id}', response={204: None, 400: DetailOut})
def delete_entry(request, entry_id: int):
    entry = own_entry_or_403(request, entry_id)
    if entry.is_running:
        return Status(400, {'detail': 'Pare o cronômetro antes de apagar.'})
    entry.delete()
    return Status(204, None)
