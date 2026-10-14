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
