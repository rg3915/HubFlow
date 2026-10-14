"""Server-Sent Events do quadro: uma conexão por projeto, alimentada pelo Redis pub/sub."""

import asyncio
import json

import redis.asyncio as aioredis
from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

from hubflow.accounts.models import Token
from hubflow.projects.models import Project

from .events import channel_for, connection

HEARTBEAT_SECONDS = 15


def format_event(event):
    return f'event: {event["type"]}\ndata: {json.dumps(event)}\n\n'


def project_event_stream(project_id, timeout=HEARTBEAT_SECONDS):
    """Gera o texto SSE do projeto; sem eventos, manda um comentário (heartbeat) a cada `timeout` segundos."""
    client = connection()
    pubsub = client.pubsub()
    pubsub.subscribe(channel_for(project_id))
    try:
        yield ': conectado\n\n'
        while True:
            message = pubsub.get_message(timeout=timeout)
            if message is None:
                yield ': ping\n\n'
            elif message['type'] == 'message':
                yield format_event(json.loads(message['data']))
    finally:
        pubsub.close()
        client.close()


async def project_event_stream_async(project_id, timeout=HEARTBEAT_SECONDS):
    """Versão assíncrona do stream, usada sob ASGI (uvicorn): não prende uma thread por conexão."""
    client = aioredis.Redis.from_url(settings.REDIS_URL)
    pubsub = client.pubsub()
    await pubsub.subscribe(channel_for(project_id))
    try:
        yield ': conectado\n\n'
        while True:
            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True, timeout=timeout), timeout + 1
                )
            except asyncio.TimeoutError:
                message = None
            if message is None:
                yield ': ping\n\n'
            elif message['type'] == 'message':
                yield format_event(json.loads(message['data']))
    finally:
        await pubsub.unsubscribe()
        await pubsub.aclose()
        await client.aclose()
        await client.connection_pool.disconnect()


@require_GET
def project_events(request, project_id):
    # EventSource não manda cabeçalhos: o token vem na query string.
    token = Token.objects.select_related('user').filter(key=request.GET.get('token', ''), user__is_active=True).first()
    if token is None:
        return HttpResponse('Não autorizado.', status=401)
    project = get_object_or_404(Project, id=project_id)
    response = StreamingHttpResponse(project_event_stream_async(project.id), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
