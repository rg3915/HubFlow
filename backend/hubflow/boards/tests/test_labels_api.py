import pytest

from hubflow.boards.models import Label

pytestmark = pytest.mark.django_db


JSON = {'content_type': 'application/json'}


def post_label(api, project, name, color='#1d4ed8'):
    return api.post(f'/api/projects/{project.id}/labels', {'name': name, 'color': color}, **JSON)


def test_cria_etiqueta_no_projeto(api, loja):
    response = post_label(api, loja, 'bug', '#a33a2e')

    assert response.status_code == 201
    label = Label.objects.get(id=response.json()['id'])
    assert response.json() == {
        'id': label.id,
        'uuid': str(label.uuid),
        'project_id': loja.id,
        'name': 'bug',
        'color': '#a33a2e',
    }


def test_nome_unico_no_projeto(api, loja):
    post_label(api, loja, 'bug')

    assert post_label(api, loja, 'Bug').status_code == 400


def test_cor_invalida_retorna_422(api, loja):
    assert post_label(api, loja, 'bug', 'vermelho').status_code == 422


def test_lista_etiquetas_em_ordem_alfabetica(api, loja):
    post_label(api, loja, 'ui')
    post_label(api, loja, 'bug')

    response = api.get(f'/api/projects/{loja.id}/labels')

    assert [label['name'] for label in response.json()] == ['bug', 'ui']


def test_edita_e_exclui_etiqueta(api, loja):
    label_id = post_label(api, loja, 'bug').json()['id']

    response = api.put(f'/api/labels/{label_id}', {'name': 'erro', 'color': '#000000'}, **JSON)
    assert response.status_code == 200
    assert Label.objects.get(id=label_id).name == 'erro'

    assert api.delete(f'/api/labels/{label_id}').status_code == 204
    assert not Label.objects.filter(id=label_id).exists()


def test_card_recebe_etiquetas(api, loja, card):
    bug = post_label(api, loja, 'bug').json()['id']
    ui = post_label(api, loja, 'ui').json()['id']

    response = api.put(f'/api/cards/{card.id}/labels', {'label_ids': [bug, ui]}, content_type='application/json')

    assert response.status_code == 200
    assert [label['name'] for label in response.json()['labels']] == ['bug', 'ui']
    assert [label['name'] for label in api.get(f'/api/cards/{card.id}').json()['labels']] == ['bug', 'ui']


def test_etiqueta_de_outro_projeto_e_recusada(api, loja, card):
    other = loja.__class__.objects.create(client=loja.client, name='App', provider='github', owner='acme', repo='app')
    foreign = post_label(api, other, 'bug').json()['id']

    response = api.put(f'/api/cards/{card.id}/labels', {'label_ids': [foreign]}, content_type='application/json')

    assert response.status_code == 400


def test_quadro_traz_as_etiquetas_dos_cards(api, loja, card):
    bug = post_label(api, loja, 'bug', '#a33a2e').json()['id']
    api.put(f'/api/cards/{card.id}/labels', {'label_ids': [bug]}, content_type='application/json')

    board = api.get(f'/api/projects/{loja.id}/board').json()

    uuid = str(Label.objects.get(id=bug).uuid)
    expected = [{'id': bug, 'uuid': uuid, 'project_id': loja.id, 'name': 'bug', 'color': '#a33a2e'}]
    assert board['columns'][0]['cards'][0]['labels'] == expected


def test_excluir_etiqueta_tira_dos_cards(api, loja, card):
    bug = post_label(api, loja, 'bug').json()['id']
    api.put(f'/api/cards/{card.id}/labels', {'label_ids': [bug]}, content_type='application/json')

    api.delete(f'/api/labels/{bug}')

    assert api.get(f'/api/cards/{card.id}').json()['labels'] == []
