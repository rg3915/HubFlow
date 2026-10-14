from ninja import Schema


class ClientBriefOut(Schema):
    id: int
    name: str


class UserAccessOut(Schema):
    # Dicionário montado por describe_user (sem resolvers de UserOut, que leem o objeto).
    id: int
    email: str
    name: str
    first_name: str
    avatar_url: str | None
    is_active: bool
    is_superuser: bool
    roles: list[str]
    permissions: list[str]
    extra_permissions: list[str]
    clients: list[ClientBriefOut]


class InviteIn(Schema):
    email: str
    name: str = ''
    roles: list[str] = []
    client_ids: list[int] = []


class RolesIn(Schema):
    roles: list[str]


class PermissionsIn(Schema):
    permissions: list[str]


class ClientsIn(Schema):
    client_ids: list[int]


class ActiveIn(Schema):
    is_active: bool


class RoleOut(Schema):
    name: str
    permissions: list[str]


class PermissionOut(Schema):
    code: str
    label: str


class CatalogOut(Schema):
    roles: list[RoleOut]
    permissions: list[PermissionOut]
