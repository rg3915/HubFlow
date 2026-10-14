import pytest
from django.contrib.auth import get_user_model

from hubflow.automations.models import Automation
from hubflow.boards.models import Card, CardEvent, Label, Notification

pytestmark = pytest.mark.django_db

JSON = {'content_type': 'application/json'}


def rule(loja, **data):
    return Automation.objects.create(project=loja, name=data.pop('name', 'Regra'), **data)


def new_card(api, loja, title='Login'):
    return Card.objects.get(id=api.post(f'/api/projects/{loja.id}/cards', {'title': title}, **JSON).json()['id'])


def move(api, card, column):
    return api.post(f'/api/cards/{card.id}/move', {'column': column}, **JSON)


def test_card_criado_define_responsavel_e_etiqueta(api, loja, user):
    bob = get_user_model().objects.create_user(email='bob@hubflow.com', password='x', name='Bob')
    bug = Label.objects.create(project=loja, name='triagem')
    rule(loja, trigger='created', action='assign', action_user=bob)
    rule(loja, trigger='created', action='add_label', action_label=bug)

    card = new_card(api, loja)

    assert card.assignee == bob
    assert list(card.labels.values_list('name', flat=True)) == ['triagem']
    events = CardEvent.objects.filter(card=card, kind='automation').order_by('id')
    assert [e.data['description'] for e in events] == [
        'Quando um card for criado → definir Bob como responsável',
        'Quando um card for criado → adicionar a etiqueta triagem',
    ]


def test_entrar_na_coluna_move_para_outra(api, loja):
    rule(loja, trigger='entered_column', trigger_column='qa', action='move', action_column='done')
    card = new_card(api, loja)

    move(api, card, 'qa')

    card.refresh_from_db()
    assert card.column == 'done'


def test_acao_de_automacao_nao_dispara_outra(api, loja):
    rule(loja, trigger='entered_column', trigger_column='qa', action='move', action_column='done')
    rule(loja, trigger='entered_column', trigger_column='done', action='move', action_column='qa')
    card = new_card(api, loja)

    move(api, card, 'qa')

    card.refresh_from_db()
    assert card.column == 'done'
    assert CardEvent.objects.filter(card=card, kind='automation').count() == 1


def test_avisar_notifica_criador_e_responsavel(api, loja, user):
    bob = get_user_model().objects.create_user(email='bob@hubflow.com', password='x', name='Bob')
    rule(loja, trigger='entered_column', trigger_column='doing', action='notify', name='Avisar início')
    card = new_card(api, loja)
    card.assignee = bob
    card.save()

    move(api, card, 'doing')

    note = Notification.objects.get(user=bob, kind='automation')
    assert 'Avisar início' in note.text and f'#{card.number}' in note.text
    assert Notification.objects.filter(user=user, kind='automation').exists()  # criador também


def test_desligada_ou_de_outro_gatilho_nao_roda(api, loja, user):
    rule(loja, trigger='created', action='assign', action_user=user, is_active=False)
    rule(loja, trigger='entered_column', trigger_column='qa', action='move', action_column='done')

    card = new_card(api, loja)
    move(api, card, 'doing')

    card.refresh_from_db()
    assert card.assignee is None and card.column == 'doing'
