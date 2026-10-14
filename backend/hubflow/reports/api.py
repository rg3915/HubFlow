from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router, Status

from hubflow.accounts.schemas import DetailOut
from hubflow.permissions.services import visible_clients, visible_projects

from .mail import send_report_email
from .models import ReportSchedule
from .pdf import file_name, render_report_pdf
from .schemas import ReportOut, ReportSendIn, ScheduleIn, ScheduleOut, SentOut
from .services import PERIODS, default_recipients, last_finished_period, report_for

router = Router(tags=['reports'])
schedules_router = Router(tags=['reports'])


@router.get('', response=ReportOut)
def get_report(
    request,
    client: int | None = None,
    project: int | None = None,
    period: str | None = None,
    date: date | None = None,
    start: date | None = None,
    end: date | None = None,
):
    return report_for(request.user, client, project, period, date, start, end)


@router.get('/pdf')
def get_report_pdf(
    request,
    client: int | None = None,
    project: int | None = None,
    period: str | None = None,
    date: date | None = None,
    start: date | None = None,
    end: date | None = None,
):
    report = report_for(request.user, client, project, period, date, start, end)
    response = HttpResponse(render_report_pdf(report), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{file_name(report)}"'
    return response


@router.post('/send', response={200: SentOut, 400: DetailOut})
def send_report(request, data: ReportSendIn):
    recipients = data.emails or default_recipients(request.user, data.client, data.project)
    if not recipients:
        return Status(400, {'detail': 'Informe os e-mails ou cadastre e-mails no projeto ou no cliente.'})
    if error := invalid_emails(recipients):
        return error
    report = report_for(request.user, data.client, data.project, data.period, data.date, data.start, data.end)
    send_report_email(report, recipients)
    return {'sent_to': recipients}


def invalid_emails(emails):
    for email in emails:
        try:
            validate_email(email)
        except ValidationError:
            return Status(400, {'detail': f'E-mail inválido: {email}'})
    return None


def save_schedule(request, schedule, data):
    """Cliente ou projeto visível, frequência conhecida e e-mails válidos; devolve 400 quando algo não serve."""
    if not (data.client or data.project):
        return Status(400, {'detail': 'Escolha o cliente ou o projeto do relatório.'})
    if data.frequency not in PERIODS:
        return Status(400, {'detail': f'Frequência: {", ".join(PERIODS)}.'})
    if error := invalid_emails(data.emails):
        return error
    schedule.client = get_object_or_404(visible_clients(request.user), id=data.client) if data.client else None
    schedule.project = get_object_or_404(visible_projects(request.user), id=data.project) if data.project else None
    if schedule.frequency != data.frequency or schedule.last_period_end is None:
        # primeiro envio no fim do período atual (não manda um período velho ao criar)
        schedule.last_period_end = last_finished_period(data.frequency, timezone.localdate())[1]
    schedule.frequency, schedule.emails, schedule.is_active = data.frequency, data.emails, data.is_active
    schedule.save()
    return None


def own_schedules(request):
    return ReportSchedule.objects.filter(created_by=request.user).select_related('client', 'project')


@schedules_router.get('', response=list[ScheduleOut])
def list_schedules(request):
    return own_schedules(request)


@schedules_router.post('', response={201: ScheduleOut, 400: DetailOut})
def add_schedule(request, data: ScheduleIn):
    schedule = ReportSchedule(created_by=request.user)
    return save_schedule(request, schedule, data) or Status(201, schedule)


@schedules_router.put('/{schedule_id}', response={200: ScheduleOut, 400: DetailOut})
def update_schedule(request, schedule_id: int, data: ScheduleIn):
    schedule = get_object_or_404(own_schedules(request), id=schedule_id)
    return save_schedule(request, schedule, data) or schedule


@schedules_router.delete('/{schedule_id}', response={204: None})
def delete_schedule(request, schedule_id: int):
    get_object_or_404(own_schedules(request), id=schedule_id).delete()
    return Status(204, None)
