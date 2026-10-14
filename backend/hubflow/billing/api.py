from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.accounts.schemas import DetailOut
from hubflow.permissions.services import require, require_payments_view, visible_payments, visible_project_or_404
from hubflow.sprints.models import Sprint

from .models import Payment, month_bounds
from .schemas import PaymentIn, PaymentOut, SummaryOut
from .summary import payments_summary

router = Router(tags=['payments'])


def payment_queryset(user):
    return visible_payments(user).select_related('project__client', 'sprint')


def payment_for(request, payment_id, perm):
    """Pagamento visível para a pessoa (404 fora do escopo) e a permissão exigida para a ação (403)."""
    payment = get_object_or_404(payment_queryset(request.user), id=payment_id)
    require(request.user, perm)
    return payment


def apply_payment_data(payment, data, user):
    """Projeto, sprint (opcional), período (mês ou datas) e demais campos; devolve 400 quando algo não serve."""
    payment.project = visible_project_or_404(user, data.project_id)
    payment.sprint = get_object_or_404(Sprint, id=data.sprint_id) if data.sprint_id else None
    payment.period_start, payment.period_end = data.period_start, data.period_end
    if data.month:
        year, month = (int(part) for part in data.month.split('-'))
        payment.period_start, payment.period_end = month_bounds(year, month)
    for field, value in data.dict(exclude={'project_id', 'sprint_id', 'month', 'period_start', 'period_end'}).items():
        setattr(payment, field, value)
    try:
        payment.clean()
    except ValidationError as error:
        return Status(400, {'detail': ' '.join(error.messages)})
    return None


@router.get('/summary', response=SummaryOut)
def summary(request, client: int | None = None, year: int | None = None):
    require_payments_view(request.user)
    return payments_summary(visible_payments(request.user), client_id=client, year=year)


@router.get('', response=list[PaymentOut])
def list_payments(request, client: int | None = None, status: str | None = None, year: int | None = None):
    require_payments_view(request.user)
    payments = payment_queryset(request.user)
    if client is not None:
        payments = payments.filter(project__client_id=client)
    if status:
        payments = payments.filter(status=status)
    if year:
        payments = payments.filter(issue_date__year=year)
    return payments


@router.post('', response={201: PaymentOut, 400: DetailOut})
def create_payment(request, data: PaymentIn):
    require(request.user, 'billing.add_payment')
    payment = Payment()
    if error := apply_payment_data(payment, data, request.user):
        return error
    payment.save()
    return Status(201, payment_queryset(request.user).get(id=payment.id))


@router.get('/{payment_id}', response=PaymentOut)
def get_payment(request, payment_id: int):
    require_payments_view(request.user)
    return get_object_or_404(payment_queryset(request.user), id=payment_id)


@router.put('/{payment_id}', response={200: PaymentOut, 400: DetailOut})
def update_payment(request, payment_id: int, data: PaymentIn):
    payment = payment_for(request, payment_id, 'billing.change_payment')
    if error := apply_payment_data(payment, data, request.user):
        return error
    payment.save()
    return payment


@router.delete('/{payment_id}', response={204: None})
def delete_payment(request, payment_id: int):
    payment_for(request, payment_id, 'billing.delete_payment').delete()
    return Status(204, None)


@router.post('/{payment_id}/pay', response=PaymentOut)
def pay(request, payment_id: int):
    payment = payment_for(request, payment_id, 'billing.change_payment')
    payment.pay()  # RN-81
    return payment


@router.post('/{payment_id}/copy', response={201: PaymentOut})
def copy(request, payment_id: int):
    payment = payment_for(request, payment_id, 'billing.change_payment')
    return Status(201, payment_queryset(request.user).get(id=payment.copy().id))
