from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.accounts.schemas import DetailOut
from hubflow.accounts.services import send_invite_email
from hubflow.clients.models import Client

from .catalog import ALL, LABELS, ROLES
from .models import Membership, PermissionChange
from .schemas import (
    ActiveIn,
    CatalogOut,
    ClientsIn,
    InviteIn,
    PermissionChangeOut,
    PermissionsIn,
    RolesIn,
    UserAccessOut,
)
from .services import describe_user, require, users_with_access

router = Router(tags=['users'])
MANAGE = 'accounts.change_user'


def managed_user(request, user_id):
    require(request.user, MANAGE)
    return get_object_or_404(users_with_access(), id=user_id)


def log_change(request, user, action, before, after):
    if before != after:
        PermissionChange.objects.create(user=user, action=action, before=before, after=after, created_by=request.user)


def fresh(user_id):
    return describe_user(users_with_access().get(id=user_id))


@router.get('/users/manage', response=list[UserAccessOut])
def list_users_access(request):
    require(request.user, MANAGE)
    return [describe_user(user) for user in users_with_access()]


@router.get('/users/changes', response=list[PermissionChangeOut])
def list_changes(request, user: int | None = None):
    require(request.user, MANAGE)
    changes = PermissionChange.objects.select_related('user', 'created_by')
    return (changes.filter(user_id=user) if user else changes)[:200]


@router.get('/users/catalog', response=CatalogOut)
def catalog(request):
    require(request.user, MANAGE)
    return {
        'roles': [{'name': name, 'permissions': perms} for name, perms in ROLES.items()],
        'permissions': [{'code': code, 'label': label} for code, label in LABELS.items()],
    }


def unknown_roles(names):
    unknown = [name for name in names if name not in ROLES]
    return Status(400, {'detail': f'Papel desconhecido: {", ".join(unknown)}.'}) if unknown else None


def link_clients(user, client_ids):
    clients = Client.objects.filter(id__in=client_ids)
    Membership.objects.filter(user=user).exclude(client__in=clients).delete()
    for client in clients:
        Membership.objects.get_or_create(user=user, client=client)


@router.post('/users/invite', response={201: UserAccessOut, 400: DetailOut})
def invite(request, data: InviteIn):
    """Cria a pessoa sem senha (papéis e clientes) e manda o link para ela definir a senha."""
    require(request.user, 'accounts.add_user')
    if error := unknown_roles(data.roles):
        return error
    User = get_user_model()
    email = data.email.strip().lower()
    try:
        validate_email(email)
    except ValidationError:
        return Status(400, {'detail': 'Informe um e-mail válido.'})
    if User.objects.filter(email=email).exists():
        return Status(400, {'detail': 'Já existe uma pessoa com este e-mail.'})
    with transaction.atomic():
        user = User.objects.create_user(email=email, name=data.name)  # sem senha até aceitar o convite
        user.groups.set(Group.objects.filter(name__in=data.roles))
        link_clients(user, data.client_ids)
        log_change(request, user, 'invite', [], sorted(data.roles))
    send_invite_email(user, request.user)
    return Status(201, fresh(user.id))


@router.put('/users/{user_id}/roles', response={200: UserAccessOut, 400: DetailOut})
def set_roles(request, user_id: int, data: RolesIn):
    user = managed_user(request, user_id)
    if error := unknown_roles(data.roles):
        return error
    before = describe_user(user)['roles']
    user.groups.set(Group.objects.filter(name__in=data.roles))
    after = fresh(user.id)
    log_change(request, user, 'roles', before, after['roles'])
    return after


@router.put('/users/{user_id}/permissions', response={200: UserAccessOut, 400: DetailOut})
def set_permissions(request, user_id: int, data: PermissionsIn):
    user = managed_user(request, user_id)
    unknown = [code for code in data.permissions if code not in ALL]
    if unknown:
        return Status(400, {'detail': f'Permissão fora do catálogo: {", ".join(unknown)}.'})
    wanted = [
        Permission.objects.get(content_type__app_label=app, codename=name)
        for app, name in (c.split('.') for c in data.permissions)
    ]
    before = describe_user(user)['extra_permissions']
    user.user_permissions.set(wanted)
    after = fresh(user.id)
    log_change(request, user, 'permissions', before, after['extra_permissions'])
    return after


@router.put('/users/{user_id}/clients', response=UserAccessOut)
def set_clients(request, user_id: int, data: ClientsIn):
    user = managed_user(request, user_id)
    before = [c['name'] for c in describe_user(user)['clients']]
    link_clients(user, data.client_ids)
    after = fresh(user.id)
    log_change(request, user, 'clients', before, [c['name'] for c in after['clients']])
    return after


@router.put('/users/{user_id}/active', response={200: UserAccessOut, 400: DetailOut})
def set_active(request, user_id: int, data: ActiveIn):
    user = managed_user(request, user_id)
    if user.id == request.user.id and not data.is_active:
        return Status(400, {'detail': 'Você não pode desativar a própria conta.'})
    log_change(request, user, 'active', [user.is_active], [data.is_active])
    user.is_active = data.is_active
    user.save(update_fields=['is_active'])
    return fresh(user.id)
