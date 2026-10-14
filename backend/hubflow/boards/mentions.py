import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage

from .notifications import actor_name, card_link, card_owners, notify_in_app

MENTION = re.compile(r'@([\w.+-]+@[\w.-]+\.\w+|[\w.-]+)')


def find_mentioned(text, author):
    """Usuários ativos citados como @email ou @nome (sem diferenciar maiúsculas), exceto o próprio autor."""
    handles = {h.lower().rstrip('.') for h in MENTION.findall(text)}
    if not handles:
        return []
    users = get_user_model().objects.filter(is_active=True).exclude(id=author.id)
    return [u for u in users if u.email in handles or (u.name and u.name.split()[0].lower() in handles)]


def notify_mentions(comment):
    """Guarda as menções, avisa cada mencionado por e-mail e no sino, e os donos do card no sino."""
    mentioned = find_mentioned(comment.text, comment.author)
    comment.mentions.set(mentioned)
    card = comment.card
    author = actor_name(comment.author)
    title = f'#{card.number} {card.title}'
    notified = notify_in_app(mentioned, 'mention', card, f'{author} mencionou você em {title}', comment.author)
    owners = [u for u in card_owners(card) if u and u.id not in notified]
    notify_in_app(owners, 'comment', card, f'{author} comentou em {title}', comment.author)
    for user in mentioned:
        where = f'{card.project.client.name} / {card.project.name}'
        body = (
            f'{author} mencionou você em um comentário do card #{card.number} {card.title} ({where}):\n\n'
            f'{comment.text}\n\nAbrir o card: {card_link(card)}\n'
        )
        subject = f'[HubFlow] {author} mencionou você em #{card.number} {card.title}'
        EmailMessage(subject=subject, body=body, to=[user.email], from_email=settings.DEFAULT_FROM_EMAIL).send()
    return mentioned
