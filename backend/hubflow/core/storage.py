"""Onde ficam os arquivos enviados (anexos e avatares): disco local (padrão) ou S3 (AWS ou compatível)."""

from django.core.exceptions import ImproperlyConfigured

LOCAL = {'BACKEND': 'django.core.files.storage.FileSystemStorage'}
STATIC = {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}


def storages_for(backend, env):
    """Monta STORAGES a partir de STORAGE_BACKEND e das variáveis AWS_* (env = dicionário de variáveis)."""
    if backend == 'local':
        return {'default': LOCAL, 'staticfiles': STATIC}
    if backend != 's3':
        raise ImproperlyConfigured(f'STORAGE_BACKEND deve ser "local" ou "s3", não "{backend}".')
    if not env.get('AWS_STORAGE_BUCKET_NAME'):
        raise ImproperlyConfigured('Com STORAGE_BACKEND=s3, defina AWS_STORAGE_BUCKET_NAME.')
    options = {
        'bucket_name': env['AWS_STORAGE_BUCKET_NAME'],
        'endpoint_url': env.get('AWS_S3_ENDPOINT_URL') or None,  # vazio = AWS; local: http://s3:8333
        'access_key': env.get('AWS_ACCESS_KEY_ID') or None,
        'secret_key': env.get('AWS_SECRET_ACCESS_KEY') or None,
        'region_name': env.get('AWS_S3_REGION_NAME') or None,
        # Com domínio público (bucket legível, ex.: S3 local em dev) as URLs não são assinadas.
        'custom_domain': env.get('AWS_S3_CUSTOM_DOMAIN') or None,
        'url_protocol': env.get('AWS_S3_URL_PROTOCOL') or 'https:',
        'querystring_auth': not env.get('AWS_S3_CUSTOM_DOMAIN'),
        'file_overwrite': False,
    }
    return {'default': {'BACKEND': 'storages.backends.s3.S3Storage', 'OPTIONS': options}, 'staticfiles': STATIC}
