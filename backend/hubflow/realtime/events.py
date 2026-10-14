"""Eventos do quadro via Redis pub/sub: a API publica, as conexões SSE assinam."""

import json
from contextlib import contextmanager

import redis
from django.conf import settings


def channel_for(project_id):
    return f'hubflow:project:{project_id}'


def connection():
    return redis.Redis.from_url(settings.REDIS_URL)


def publish(project_id, event_type, data):
    """Publica um evento no canal do projeto. Falha no Redis não derruba a API (só perde o aviso ao vivo)."""
    message = json.dumps({'type': event_type, 'project_id': project_id, 'data': data}, default=str)
    try:
        connection().publish(channel_for(project_id), message)
    except redis.RedisError:
        pass


@contextmanager
def subscribe(project_id, timeout=5):
    """Gerador síncrono de eventos do projeto (usado nos testes e em scripts)."""
    client = connection()
    pubsub = client.pubsub()
    pubsub.subscribe(channel_for(project_id))
    # Espera a confirmação do SUBSCRIBE: um publish logo em seguida não pode chegar antes de estarmos ouvindo.
    while (confirmation := pubsub.get_message(timeout=timeout)) and confirmation['type'] != 'subscribe':
        pass

    def messages():
        while True:
            message = pubsub.get_message(timeout=timeout)
            if message is None:
                return
            if message['type'] == 'message':
                yield json.loads(message['data'])

    try:
        yield messages()
    finally:
        pubsub.close()
        client.close()
