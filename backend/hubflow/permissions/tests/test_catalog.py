import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import IntegrityError

from hubflow.clients.models import Client
from hubflow.permissions.catalog import PERMISSIONS, ROLES
from hubflow.permissions.models import Membership
from hubflow.permissions.services import effective_permissions, has_perm

pytestmark = pytest.mark.django_db

User = get_user_model()


def test_catalogo_tem_as_permissoes_combinadas():
    assert set(PERMISSIONS) == {
        'view_all_clients',
        'manage_projects',
        'create_cards',
        'edit_any_card',
        'delete_any_card',
        'delete_any_comment',
        'manage_sprints',
        'manage_labels',
        'view_all_payments',
        'view_own_payments',
        'manage_payments',
        'use_cli',
        'manage_users',
    }
    assert PERMISSIONS['use_cli'] == 'Usar a CLI'


def test_permissoes_existem_no_banco_apos_migrar():
    codenames = set(
        Permission.objects.filter(content_type__app_label='permissions').values_list('codename', flat=True)
    )

    assert set(PERMISSIONS) <= codenames


def test_papeis_padrao_existem_com_as_permissoes_do_catalogo():
    assert set(ROLES) == {'Administrador', 'Gerente', 'Desenvolvedor', 'Financeiro', 'Cliente', 'Leitura'}
    for name, codenames in ROLES.items():
        group = Group.objects.get(name=name)
        assert set(group.permissions.values_list('codename', flat=True)) == set(codenames), name
    assert set(ROLES['Administrador']) == set(PERMISSIONS)
    assert 'use_cli' in ROLES['Desenvolvedor'] and 'view_all_payments' not in ROLES['Desenvolvedor']
    assert 'view_own_payments' in ROLES['Cliente'] and 'create_cards' not in ROLES['Cliente']


def test_permissoes_efetivas_vem_do_papel_e_da_pessoa():
    user = User.objects.create_user(email='dev@hubflow.com', password='x')
    user.groups.add(Group.objects.get(name='Desenvolvedor'))
    user.user_permissions.add(Permission.objects.get(codename='view_all_payments'))

    perms = effective_permissions(user)

    assert 'create_cards' in perms and 'view_all_payments' in perms and 'manage_users' not in perms
    assert has_perm(user, 'use_cli') is True
    assert has_perm(user, 'manage_users') is False


def test_superusuario_tem_tudo():
    admin = User.objects.create_superuser(email='admin@hubflow.com', password='x')

    assert effective_permissions(admin) == set(PERMISSIONS)


def test_vinculo_usuario_cliente_e_unico():
    user = User.objects.create_user(email='dev@hubflow.com', password='x')
    acme = Client.objects.create(name='ACME')
    Membership.objects.create(user=user, client=acme)

    with pytest.raises(IntegrityError):
        Membership.objects.create(user=user, client=acme)


def test_clientes_da_pessoa():
    user = User.objects.create_user(email='dev@hubflow.com', password='x')
    acme = Client.objects.create(name='ACME')
    Client.objects.create(name='Beta')
    Membership.objects.create(user=user, client=acme)

    assert list(user.memberships.values_list('client__name', flat=True)) == ['ACME']
