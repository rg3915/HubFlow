from datetime import timedelta

from django.utils import timezone

from .models import TimeEntry

CONTINUITY_WINDOW = timedelta(minutes=15)


def start_timer(card, user):
    """Abre o cronômetro do card (RN-70). RN-71: se o mesmo usuário parou há menos de 15 min no mesmo
    projeto, o novo começa onde o anterior terminou, sem buraco entre eles."""
    started_at = timezone.now()
    # Só cronômetros já encerrados contam; lançamentos manuais têm horário fictício (09:00 do dia).
    last = (
        TimeEntry.objects.filter(user=user, card__project_id=card.project_id, is_manual=False)
        .filter(ended_at__isnull=False, ended_at__lte=started_at)
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


def project_median_estimate(project_id):
    """RN-75: mediana das horas gastas nos cards concluídos do projeto (None sem histórico)."""
    from statistics import median

    from django.db.models import F, Sum

    from hubflow.boards.models import Column

    totals = (
        TimeEntry.objects.filter(card__project_id=project_id, card__column=Column.DONE, ended_at__isnull=False)
        .values('card_id')
        .annotate(total=Sum(F('ended_at') - F('started_at')))
        .values_list('total', flat=True)
    )
    hours = [t.total_seconds() / 3600 for t in totals if t]
    return round(median(hours), 2) if hours else None


def card_progress(card, spent_hours, median_hours):
    """Gasto × estimado: estimativa do card ou, na falta, a mediana do projeto."""
    if card.estimate_hours:
        estimate, source = card.estimate_hours, 'card'
    elif median_hours:
        estimate, source = median_hours, 'median'
    else:
        return {'spent_hours': spent_hours, 'estimate_hours': None, 'percent': None, 'source': None}
    return {
        'spent_hours': spent_hours,
        'estimate_hours': estimate,
        'percent': round(spent_hours / estimate * 100),
        'source': source,
    }
