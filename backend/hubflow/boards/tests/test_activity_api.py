import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


@pytest.fixture(autouse=True)
def media_tmp(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def bob(db):
    return get_user_model().objects.create_user(email='bob@example.com', password='segredo123', name='Bob')


def activity(api, card):
    return api.get(f'/api/cards/{card.id}/activity').json()


def kinds(api, card):
    return [a['kind'] for a in activity(api, card)]


def test_card_novo_tem_so_a_criacao(api, loja):
    card_id = api.post(f'/api/projects/{loja.id}/cards', {'title': 'Novo'}, **JSON).json()['id']

    response = api.get(f'/api/cards/{card_id}/activity')

    assert response.status_code == 200
    assert [a['kind'] for a in response.json()] == ['created']
    assert response.json()[0]['user']['email'] == 'ana@example.com'


def test_movimentacao_comentario_e_anexo_entram_no_historico(api, card):
    api.post(f'/api/cards/{card.id}/move', {'column': 'qa'}, **JSON)
    api.post(f'/api/cards/{card.id}/comments', {'text': 'Testado'}, **JSON)
    api.post(f'/api/cards/{card.id}/attachments', {'file': SimpleUploadedFile('a.txt', b'a')})

    items = activity(api, card)

    assert [a['kind'] for a in items] == ['attachment', 'comment', 'moved']
    assert items[2]['data'] == {'from_column': 'backlog', 'to_column': 'qa'}
    assert items[1]['data'] == {'text': 'Testado'}
    assert items[0]['data'] == {'name': 'a.txt'}


def test_mudancas_de_responsavel_prazo_e_etiquetas_entram(api, loja, card, bob):
    api.put(f'/api/cards/{card.id}', {'title': card.title, 'due_date': '2026-10-20', 'assignee_id': bob.id}, **JSON)
    bug = api.post(f'/api/projects/{loja.id}/labels', {'name': 'bug', 'color': '#a33a2e'}, **JSON).json()['id']
    api.put(f'/api/cards/{card.id}/labels', {'label_ids': [bug]}, **JSON)

    items = activity(api, card)

    assert [a['kind'] for a in items] == ['labels', 'due_date', 'assignee']
    assert items[0]['data'] == {'labels': ['bug']}
    assert items[1]['data'] == {'due_date': '2026-10-20'}
    assert items[2]['data'] == {'assignee': 'bob@example.com'}


def test_editar_sem_mudar_prazo_nem_responsavel_nao_registra(api, card):
    api.put(f'/api/cards/{card.id}', {'title': 'Outro título'}, **JSON)

    assert kinds(api, card) == []


def test_historico_vem_do_mais_recente_para_o_mais_antigo(api, card):
    api.post(f'/api/cards/{card.id}/comments', {'text': 'Primeiro'}, **JSON)
    api.post(f'/api/cards/{card.id}/move', {'column': 'doing'}, **JSON)

    items = activity(api, card)

    assert [a['kind'] for a in items] == ['moved', 'comment']
    assert items[0]['created'] >= items[1]['created']


def test_card_inexistente_retorna_404(api, loja):
    assert api.get('/api/cards/999/activity').status_code == 404
