from ninja import Schema


class LoginIn(Schema):
    email: str
    password: str


class TokenOut(Schema):
    token: str
