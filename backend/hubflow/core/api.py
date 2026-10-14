from ninja import Router, Status
from ninja.errors import HttpError

from hubflow.accounts.schemas import DetailOut

from .backups import BackupError, describe, list_backups, run_backup
from .schemas import BackupOut

router = Router(tags=['backups'])


def superuser_or_403(request):
    if not request.user.is_superuser:
        raise HttpError(403, 'Só superusuários mexem nos backups.')


@router.post('', response={201: BackupOut, 400: DetailOut})
def create_backup(request):
    superuser_or_403(request)
    try:
        return Status(201, describe(run_backup()))
    except BackupError as error:
        return Status(400, {'detail': str(error)})


@router.get('', response=list[BackupOut])
def backups(request):
    superuser_or_403(request)
    return list_backups()
