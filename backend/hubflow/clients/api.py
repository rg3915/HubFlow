from django.shortcuts import get_object_or_404
from ninja import Router, Status

from hubflow.accounts.schemas import DetailOut
from hubflow.permissions.services import require, visible_clients

from .models import Client
from .schemas import ClientIn, ClientOut

router = Router(tags=['clients'])


def name_taken(name, exclude_id=None):
    return Client.objects.filter(name=name).exclude(id=exclude_id).exists()


@router.get('', response=list[ClientOut])
def list_clients(request):
    return visible_clients(request.user)


@router.post('', response={201: ClientOut, 400: DetailOut})
def create_client(request, data: ClientIn):
    require(request.user, 'clients.add_client')
    if name_taken(data.name):  # RN-10
        return Status(400, {'detail': 'Já existe um cliente com este nome.'})
    return Status(201, Client.objects.create(**data.dict()))


@router.get('/{client_id}', response=ClientOut)
def get_client(request, client_id: int):
    return get_object_or_404(visible_clients(request.user), id=client_id)


@router.put('/{client_id}', response={200: ClientOut, 400: DetailOut})
def update_client(request, client_id: int, data: ClientIn):
    require(request.user, 'clients.change_client')
    client = get_object_or_404(visible_clients(request.user), id=client_id)
    if name_taken(data.name, exclude_id=client.id):
        return Status(400, {'detail': 'Já existe um cliente com este nome.'})
    for field, value in data.dict().items():
        setattr(client, field, value)
    client.save()
    return client


@router.delete('/{client_id}', response={204: None, 400: DetailOut})
def delete_client(request, client_id: int):
    require(request.user, 'clients.delete_client')
    client = get_object_or_404(visible_clients(request.user), id=client_id)
    if client.projects.exists():  # RN-11
        return Status(400, {'detail': 'Este cliente tem projetos. Arquive-o em vez de excluir.'})
    client.delete()
    return Status(204, None)
