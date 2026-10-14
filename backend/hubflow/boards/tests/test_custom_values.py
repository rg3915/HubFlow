import pytest

from hubflow.boards.models import Card, CardEvent, CustomField

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


@pytest.fixture
def fields(loja):
    return {
        'prioridade': CustomField.objects.create(
            project=loja, name='Prioridade', kind='select', options=['Alta', 'Baixa'], required=True
        ),
        'pontos': CustomField.objects.create(project=loja, name='Pontos', kind='number'),
        'entrega': CustomField.objects.create(project=loja, name='Entrega', kind='date'),
        'urgente': CustomField.objects.create(project=loja, name='Urgente', kind='bool'),
        'obs': CustomField.objects.create(project=loja, name='Obs', kind='text'),
    }


def create(api, loja, values):
    return api.post(f'/api/projects/{loja.id}/cards', {'title': 'Login', 'fields': values}, **JSON)


def ids(fields, **values):
    return {str(fields[key].id): value for key, value in values.items()}


def test_cria_card_com_valores(api, loja, fields):
    values = ids(fields, prioridade='Alta', pontos=3.5, entrega='2026-11-01', urgente=True, obs='VIP')

    response = create(api, loja, values)

    assert response.status_code == 201, response.json()
    assert response.json()['custom_values'] == values
    assert Card.objects.get().custom_values == values


@pytest.mark.parametrize(
    ('values', 'message'),
    [
        ({'pontos': 2}, 'Prioridade'),  # obrigatório faltando
        ({'prioridade': 'Média'}, 'opção'),
        ({'prioridade': 'Alta', 'pontos': 'três'}, 'número'),
        ({'prioridade': 'Alta', 'entrega': '01/11/2026'}, 'data'),
        ({'prioridade': 'Alta', 'urgente': 'sim'}, 'sim/não'),
    ],
)
def test_valores_invalidos_retornam_400(api, loja, fields, values, message):
    response = create(api, loja, ids(fields, **values))

    assert response.status_code == 400
    assert message in response.json()['detail']
    assert not Card.objects.exists()


def test_campo_de_outro_projeto_retorna_400(api, loja, fields):
    response = create(api, loja, ids(fields, prioridade='Alta') | {'999999': 'x'})

    assert response.status_code == 400 and 'desconhecido' in response.json()['detail']


def test_edita_valores_e_registra_no_historico(api, loja, fields, user):
    card_id = create(api, loja, ids(fields, prioridade='Alta', obs='VIP')).json()['id']

    response = api.put(
        f'/api/cards/{card_id}', {'title': 'Login', 'fields': ids(fields, prioridade='Baixa', obs='')}, **JSON
    )

    assert response.json()['custom_values'] == ids(fields, prioridade='Baixa')
    event = CardEvent.objects.get(kind='fields')
    assert event.data == {'changes': {'Prioridade': ['Alta', 'Baixa'], 'Obs': ['VIP', None]}}


def test_editar_sem_mandar_campos_mantem_os_valores(api, loja, fields):
    card_id = create(api, loja, ids(fields, prioridade='Alta')).json()['id']

    response = api.put(f'/api/cards/{card_id}', {'title': 'Outro título'}, **JSON)

    assert response.json()['custom_values'] == ids(fields, prioridade='Alta')


def test_nao_esvazia_obrigatorio(api, loja, fields):
    card_id = create(api, loja, ids(fields, prioridade='Alta')).json()['id']

    response = api.put(f'/api/cards/{card_id}', {'title': 'Login', 'fields': ids(fields, prioridade=None)}, **JSON)

    assert response.status_code == 400 and 'Prioridade' in response.json()['detail']


def test_card_sem_campos_continua_funcionando(api, loja):
    response = api.post(f'/api/projects/{loja.id}/cards', {'title': 'Simples'}, **JSON)

    assert response.status_code == 201 and response.json()['custom_values'] == {}
