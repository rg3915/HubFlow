from ninja import Schema


class LoginIn(Schema):
    email: str
    password: str


class TokenOut(Schema):
    token: str


class UserOut(Schema):
    id: int
    email: str
    name: str
    first_name: str
    avatar_url: str | None

    @staticmethod
    def resolve_avatar_url(user):
        return user.avatar.url if user.avatar else None


class ForgotPasswordIn(Schema):
    email: str


class DetailOut(Schema):
    detail: str


class ResetPasswordIn(Schema):
    uid: str
    token: str
    password: str


class ChangePasswordIn(Schema):
    current_password: str
    new_password: str


class MeOut(Schema):
    """Montado a partir de um dicionário (sem os resolvers do UserOut)."""

    id: int
    email: str
    name: str
    first_name: str
    avatar_url: str | None
    is_superuser: bool
    roles: list[str]
    permissions: list[str]
