from ninja import NinjaAPI

from hubflow.accounts.api import router as accounts_router

api = NinjaAPI(title='HubFlow API', version='0.1.0')

api.add_router('/auth', accounts_router)


@api.get('/health', auth=None)
def health(request):
    return {'status': 'ok'}
