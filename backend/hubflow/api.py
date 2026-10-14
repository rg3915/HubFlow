from ninja import NinjaAPI

api = NinjaAPI(title='HubFlow API', version='0.1.0')


@api.get('/health', auth=None)
def health(request):
    return {'status': 'ok'}
