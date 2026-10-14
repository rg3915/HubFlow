from .catalog import ALL


def effective_permissions(user):
    """Permissões 'app.codename' do catálogo que a pessoa tem (papéis + por pessoa); superusuário tem todas."""
    if user.is_superuser:
        return set(ALL)
    return user.get_all_permissions() & set(ALL)


def has_perm(user, perm):
    """`perm` no formato 'app.codename' (ex.: 'boards.change_card')."""
    return perm in effective_permissions(user)


def require(user, perm):
    """Levanta 403 com mensagem clara quando a pessoa não tem a permissão."""
    from ninja.errors import HttpError

    from .catalog import LABELS

    if not has_perm(user, perm):
        raise HttpError(403, f'Você não tem permissão para isto ({LABELS.get(perm, perm)}).')


def perm_code(permission):
    return f'{permission.content_type.app_label}.{permission.codename}'


def describe_user(user):
    """Papéis, permissões efetivas, permissões por pessoa e clientes, a partir dos relacionamentos já prefetchados."""
    roles = sorted(group.name for group in user.groups.all())
    from_roles = {perm_code(p) for group in user.groups.all() for p in group.permissions.all()}
    extra = sorted(perm_code(p) for p in user.user_permissions.all())
    effective = set(ALL) if user.is_superuser else (from_roles | set(extra)) & set(ALL)
    return {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'first_name': user.first_name,
        'avatar_url': user.avatar.url if user.avatar else None,
        'is_active': user.is_active,
        'is_superuser': user.is_superuser,
        'roles': roles,
        'permissions': sorted(effective),
        'extra_permissions': extra,
        'clients': [{'id': m.client_id, 'name': m.client.name} for m in user.memberships.all()],
    }


def users_with_access():
    from django.contrib.auth import get_user_model

    return (
        get_user_model()
        .objects.prefetch_related(
            'groups__permissions__content_type', 'user_permissions__content_type', 'memberships__client'
        )
        .order_by('email')
    )


def visible_clients(user):
    """Com `clients.view_client` vê todos; sem, só os clientes de que é membro."""
    from hubflow.clients.models import Client

    if has_perm(user, 'clients.view_client'):
        return Client.objects.all()
    return Client.objects.filter(memberships__user=user)


def visible_projects(user):
    from hubflow.projects.models import Project

    projects = Project.objects.select_related('client')
    if has_perm(user, 'clients.view_client'):
        return projects
    return projects.filter(client__memberships__user=user)


def visible_project_or_404(user, project_id):
    from django.shortcuts import get_object_or_404

    return get_object_or_404(visible_projects(user), id=project_id)


def visible_in_project_or_404(user, queryset, **lookup):
    """Objeto de um projeto que a pessoa enxerga (sprint, etiqueta, milestone...); 404 se for de cliente de fora."""
    from django.shortcuts import get_object_or_404

    return get_object_or_404(queryset.filter(project__in=visible_projects(user)), **lookup)


def is_card_owner(user, card):
    return user.id in (card.created_by_id, card.assignee_id)


def require_card_edit(user, card):
    """Sem `boards.change_card`, só edita/move os próprios cards (criado por ou responsável)."""
    if not (has_perm(user, 'boards.change_card') or is_card_owner(user, card)):
        from ninja.errors import HttpError

        raise HttpError(403, 'Você só pode editar e mover os seus próprios cards.')


def require_card_delete(user, card):
    if not (has_perm(user, 'boards.delete_card') or is_card_owner(user, card)):
        from ninja.errors import HttpError

        raise HttpError(403, 'Você só pode excluir ou arquivar os seus próprios cards.')
