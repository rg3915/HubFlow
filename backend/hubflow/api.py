from ninja import NinjaAPI

from hubflow.accounts.api import router as accounts_router
from hubflow.accounts.auth import TokenAuth
from hubflow.boards.api import router as boards_router
from hubflow.clients.api import router as clients_router
from hubflow.projects.api import router as projects_router

api = NinjaAPI(title='HubFlow API', version='0.1.0', auth=TokenAuth())

api.add_router('/auth', accounts_router)
api.add_router('/clients', clients_router)
api.add_router('/projects', projects_router)
api.add_router('', boards_router)


@api.get('/health', auth=None)
def health(request):
    return {'status': 'ok'}
