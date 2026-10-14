from django.conf import settings
from django.core.mail import EmailMessage

from .models import Column, Notification

SUBJECTS = {
    'created': 'novo card',
    'moved': 'card movido',
    'done': 'card concluído',
}


def card_link(card):
    return f'{settings.FRONTEND_URL}/projects/{card.project_id}?card={card.number}'


def notify(event, card, from_column=None, to_column=None):
    """Avisa os destinatários do projeto sobre um evento do card (RN-40, RN-41, RN-42).

    Único ponto de envio: API, CLI e arrastar-e-soltar chegam aqui pelo mesmo serviço.
    """
    project = card.project
    if not getattr(project, f'notify_on_{event}'):
        return
    recipients = project.notification_emails
    if not recipients:
        return

    client = project.client.name
    lines = [
        f'Cliente: {client}',
        f'Projeto: {project.name}',
        f'Card: #{card.number} {card.title}',
    ]
    if event == 'moved':
        lines.append(f'Movido de {Column(from_column).label} para {Column(to_column).label}.')
    lines += ['', f'Abrir o card: {card_link(card)}']

    subject = f'[HubFlow] {client} / {project.name}: {SUBJECTS[event]} #{card.number} {card.title}'
    EmailMessage(subject=subject, body='\n'.join(lines), to=recipients).send()


def notify_in_app(users, kind, card, text, actor=None):
    """Cria as notificações do sino para cada pessoa (uma vez só), menos quem fez a ação. Devolve quem recebeu."""
    recipients = {u.id: u for u in users if u and u.is_active and u != actor}
    Notification.objects.bulk_create(
        Notification(user=u, actor=actor, card=card, kind=kind, text=text[:300]) for u in recipients.values()
    )
    return set(recipients)


def card_owners(card):
    return [card.created_by, card.assignee]


def actor_name(user):
    return (user.name or user.email) if user else 'Alguém'
