from datetime import timedelta

from django.utils import timezone

from .models import TimeEntry

CONTINUITY_WINDOW = timedelta(minutes=15)


def start_timer(card, user):
    """Abre o cronômetro do card (RN-70). RN-71: se o mesmo usuário parou há menos de 15 min no mesmo
    projeto, o novo começa onde o anterior terminou, sem buraco entre eles."""
    started_at = timezone.now()
    last = (
        TimeEntry.objects.filter(user=user, card__project_id=card.project_id, ended_at__isnull=False)
        .order_by('-ended_at')
        .first()
    )
    if last and started_at - last.ended_at < CONTINUITY_WINDOW:
        started_at = last.ended_at
    entry = TimeEntry(card=card, user=user, started_at=started_at)
    entry.full_clean()
    entry.save()
    return entry


def stop_timer(card):
    """Fecha o cronômetro aberto do card; None se não houver."""
    entry = TimeEntry.objects.running_for(card)
    if entry is None:
        return None
    entry.ended_at = timezone.now()
    entry.save(update_fields=['ended_at'])
    return entry
