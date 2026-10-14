"""Exportação xlsx do timesheet de um projeto (A5 do levantamento do my-tasks)."""

from collections import defaultdict
from io import BytesIO

from django.utils import timezone
from openpyxl import Workbook

from .models import TimeEntry

ENTRY_HEADER = ('Data', 'Início', 'Fim', 'Duração (h)', 'Card', 'Título', 'Sprint', 'Usuário', 'Nota')


def timesheet_entries(project, start=None, end=None):
    entries = TimeEntry.objects.filter(card__project=project, ended_at__isnull=False).select_related(
        'card__sprint', 'user'
    )
    if start:
        entries = entries.filter(started_at__date__gte=start)
    if end:
        entries = entries.filter(started_at__date__lte=end)
    return entries.order_by('started_at', 'id')


def timesheet_workbook(project, start=None, end=None):
    """Abas: entradas fechadas e totais por dia, por mês e por sprint."""
    by_day, by_month, by_sprint = defaultdict(float), defaultdict(float), defaultdict(float)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Entradas'
    sheet.append(ENTRY_HEADER)
    for entry in timesheet_entries(project, start, end):
        started, ended = timezone.localtime(entry.started_at), timezone.localtime(entry.ended_at)
        hours = round(entry.hours, 2)
        sprint = entry.card.sprint.number if entry.card.sprint else None
        sheet.append(
            (
                started.date().isoformat(),
                started.strftime('%H:%M'),
                ended.strftime('%H:%M'),
                hours,
                f'#{entry.card.number}',
                entry.card.title,
                sprint,
                entry.user.email,
                entry.note,
            )
        )
        by_day[started.date().isoformat()] += hours
        by_month[started.strftime('%Y-%m')] += hours
        by_sprint[f'Sprint {sprint}' if sprint else 'Sem sprint'] += hours
    summaries = (('Por dia', 'Dia', by_day), ('Por mês', 'Mês', by_month), ('Por sprint', 'Sprint', by_sprint))
    for title, label, totals in summaries:
        total_sheet = workbook.create_sheet(title)
        total_sheet.append((label, 'Horas'))
        for key in sorted(totals):
            total_sheet.append((key, round(totals[key], 2)))
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
