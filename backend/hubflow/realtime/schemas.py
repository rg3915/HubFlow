from ninja import Schema

from hubflow.accounts.schemas import UserOut


class PresenceOut(Schema):
    viewers: list[UserOut]
