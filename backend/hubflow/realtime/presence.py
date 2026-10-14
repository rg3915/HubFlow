"""Quem está com o quadro aberto: chaves no Redis com TTL renovadas pelo heartbeat do navegador."""

from django.conf import settings
from django.contrib.auth import get_user_model

from .events import connection, publish


def _key(project_id, user_id):
    return f'hubflow:presence:{project_id}:{user_id}'


def _pattern(project_id):
    return f'hubflow:presence:{project_id}:*'


def touch(project_id, user_id):
    connection().set(_key(project_id, user_id), 1, ex=settings.PRESENCE_TTL_SECONDS)


def leave(project_id, user_id):
    connection().delete(_key(project_id, user_id))


def viewers(project_id):
    """Ids dos usuários presentes (chaves ainda vivas), em ordem crescente."""
    client = connection()
    ids = [int(key.decode().rsplit(':', 1)[1]) for key in client.scan_iter(_pattern(project_id))]
    return sorted(ids)


def viewer_users(project_id):
    return list(get_user_model().objects.filter(id__in=viewers(project_id), is_active=True).order_by('id'))


def clear_presence(project_id):
    client = connection()
    for key in client.scan_iter(_pattern(project_id)):
        client.delete(key)


def announce(project_id):
    from hubflow.accounts.schemas import UserOut

    users = viewer_users(project_id)
    publish(project_id, 'presence', {'viewers': [UserOut.from_orm(u).dict() for u in users]})
    return users
