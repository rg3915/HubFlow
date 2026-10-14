from .catalog import ALL


def effective_permissions(user):
    """Permissões 'app.codename' do catálogo que a pessoa tem (papéis + por pessoa); superusuário tem todas."""
    if user.is_superuser:
        return set(ALL)
    return user.get_all_permissions() & set(ALL)


def has_perm(user, perm):
    """`perm` no formato 'app.codename' (ex.: 'boards.change_card')."""
    return perm in effective_permissions(user)
