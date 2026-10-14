import json
import threading

import pytest
from asgiref.sync import async_to_sync
from django.test import Client as HttpClient

from hubflow.accounts.models import Token
from hubflow.realtime.events import publish
from hubflow.realtime.sse import format_event, project_event_stream, project_event_stream_async

pytestmark = pytest.mark.django_db


def test_formata_evento_sse():
    text = format_event({'type': 'card_moved', 'project_id': 1, 'data': {'x': 1}})

    assert text == 'event: card_moved\ndata: {"type": "card_moved", "project_id": 1, "data": {"x": 1}}\n\n'


def test_stream_entrega_eventos_do_projeto(loja):
    stream = project_event_stream(loja.id, timeout=5)
    first = next(stream)  # comentário inicial de conexão
    threading.Timer(0.3, lambda: publish(loja.id, 'card_created', {'card': {'id': 1}})).start()

    event = next(stream)

    assert first.startswith(':')
    assert event.startswith('event: card_created\n')
    assert json.loads(event.split('data: ', 1)[1])['data'] == {'card': {'id': 1}}


def test_stream_manda_heartbeat_sem_eventos(loja):
    stream = project_event_stream(loja.id, timeout=0.2)
    next(stream)

    assert next(stream).startswith(':')


def test_endpoint_sem_token_retorna_401(loja):
    response = HttpClient().get(f'/api/projects/{loja.id}/events')

    assert response.status_code == 401


def test_endpoint_com_token_na_query_responde_event_stream(loja, user):
    token = Token.objects.create(user=user).key

    response = HttpClient().get(f'/api/projects/{loja.id}/events?token={token}')

    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/event-stream')
    assert response['Cache-Control'] == 'no-cache'
    assert response.streaming and response.is_async
    response.close()


# O loop descartável do async_to_sync fecha antes do coletor de lixo liberar os sockets do redis.asyncio.
@pytest.mark.filterwarnings('ignore::ResourceWarning', 'ignore::pytest.PytestUnraisableExceptionWarning')
def test_stream_assincrono_conecta_e_fecha(loja):
    async def first_chunk():
        stream = project_event_stream_async(loja.id, timeout=0.2)
        try:
            return await anext(stream)
        finally:
            await stream.aclose()  # fecha a assinatura no Redis

    assert async_to_sync(first_chunk)().startswith(':')
