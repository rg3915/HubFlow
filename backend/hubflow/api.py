from ninja import NinjaAPI

from hubflow.accounts.api import router as accounts_router
from hubflow.accounts.api import users_router
from hubflow.accounts.auth import TokenAuth
from hubflow.billing.api import router as payments_router
from hubflow.boards.api import router as boards_router
from hubflow.clients.api import router as clients_router
from hubflow.core.api import router as backups_router
from hubflow.dashboard.api import router as dashboard_router
from hubflow.integrations.api import router as integrations_router
from hubflow.projects.api import router as projects_router
from hubflow.sprints.api import router as sprints_router
from hubflow.timetracking.api import router as time_router

api = NinjaAPI(title='HubFlow API', version='0.1.0', auth=TokenAuth())

api.add_router('/auth', accounts_router)
api.add_router('/users', users_router)
api.add_router('/clients', clients_router)
api.add_router('/projects', projects_router)
api.add_router('', boards_router)
api.add_router('', sprints_router)
api.add_router('', time_router)
api.add_router('/payments', payments_router)
api.add_router('/dashboard', dashboard_router)
api.add_router('', integrations_router)
api.add_router('/backups', backups_router)


@api.get('/health', auth=None)
def health(request):
    return {'status': 'ok'}
