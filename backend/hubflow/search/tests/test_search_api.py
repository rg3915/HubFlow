import pytest
from django.contrib.auth import get_user_model

from hubflow.boards.models import Card, Column, Label
from hubflow.clients.models import Client
from hubflow.projects.models import Project

pytestmark = pytest.mark.django_db


def search(api, q):
    return api.get('/api/search', {'q': q})


def test_q_curto_retorna_422(api):
    assert search(api, 'a').status_code == 422


def test_resposta_tem_os_cinco_grupos_vazios(api):
    response = search(api, 'zzz')

    assert response.status_code == 200
    assert response.json() == {'cards': [], 'projects': [], 'clients': [], 'users': [], 'labels': []}


def test_card_por_titulo_sem_diferenciar_maiusculas(api, card):
    found = search(api, 'LOGIN').json()['cards']

    assert found == [
        {
            'id': card.id,
            'number': card.number,
            'title': 'Corrigir login',
            'column': 'backlog',
            'project_id': card.project_id,
            'project_name': 'Loja',
            'client_name': 'ACME',
        }
    ]


def test_card_por_descricao(api, loja):
    card = Card.objects.create(project=loja, title='Checkout', description='Erro 500 no pagamento')

    assert [c['id'] for c in search(api, 'pagamento').json()['cards']] == [card.id]


def test_card_por_numero_exato(api, loja):
    Card.objects.create(project=loja, title='Um')
    second = Card.objects.create(project=loja, title='Dois')
    Card.objects.create(project=loja, title='Fala do #2 no título')  # não é o número 2

    found = search(api, '#2').json()['cards']

    assert {c['number'] for c in found} == {2, 3}
    assert second.id in {c['id'] for c in found}


def test_card_por_nome_da_coluna(api, loja):
    Card.objects.create(project=loja, title='No backlog')
    doing = Card.objects.create(project=loja, title='Em andamento', column=Column.DOING)

    assert [c['id'] for c in search(api, 'Em desenvolvimento').json()['cards']] == [doing.id]
    assert [c['id'] for c in search(api, 'concluído').json()['cards']] == []


def test_projeto_e_cliente(api, loja):
    found = search(api, 'loj').json()
    assert found['projects'] == [{'id': loja.id, 'name': 'Loja', 'client_name': 'ACME'}]

    found = search(api, 'acme').json()
    assert found['clients'] == [{'id': loja.client_id, 'name': 'ACME'}]
    assert found['projects'] == []


def test_usuarios_ativos_por_email_ou_nome(api, user):
    get_user_model().objects.create_user(email='ana.paula@example.com', password='x', name='Paula', is_active=False)

    found = search(api, 'ana').json()['users']

    assert found == [{'id': user.id, 'email': 'ana@example.com', 'name': 'Ana'}]


def test_etiqueta(api, loja):
    label = Label.objects.create(project=loja, name='Bug', color='#a33a2e')

    assert search(api, 'bug').json()['labels'] == [
        {'id': label.id, 'name': 'Bug', 'color': '#a33a2e', 'project_id': loja.id}
    ]


def test_no_maximo_dez_por_grupo(api, loja):
    for i in range(12):
        Card.objects.create(project=loja, title=f'Relatório {i}')
        Client.objects.create(name=f'Relatório Cliente {i}')

    found = search(api, 'relatório').json()

    assert len(found['cards']) == 10
    assert len(found['clients']) == 10


def test_poucas_consultas(api, loja, django_assert_max_num_queries):
    for i in range(3):
        other = Client.objects.create(name=f'Cliente {i}')
        project = Project.objects.create(client=other, name=f'Projeto {i}', provider='github', owner='o', repo=f'r{i}')
        Card.objects.create(project=project, title='Busca')
        Label.objects.create(project=project, name='Busca')

    with django_assert_max_num_queries(6):  # token + uma por tipo
        search(api, 'busca')
