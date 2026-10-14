from ninja import Field, Schema

from hubflow.accounts.schemas import UserOut
from hubflow.boards.schemas import LabelOut


class CardHit(Schema):
    id: int
    number: int
    title: str
    column: str
    project_id: int
    project_name: str = Field(alias='project.name')
    client_name: str = Field(alias='project.client.name')


class ProjectHit(Schema):
    id: int
    name: str
    client_name: str = Field(alias='client.name')


class ClientHit(Schema):
    id: int
    name: str


class SearchOut(Schema):
    cards: list[CardHit]
    projects: list[ProjectHit]
    clients: list[ClientHit]
    users: list[UserOut]
    labels: list[LabelOut]
