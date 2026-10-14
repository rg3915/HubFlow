"""Onde ficam os arquivos enviados (anexos e avatares): disco local (padrão), S3 (AWS ou compatível) ou Cloudinary."""

import posixpath
from urllib.parse import urlparse
from urllib.request import urlopen

from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

LOCAL = {'BACKEND': 'django.core.files.storage.FileSystemStorage'}
STATIC = {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}


def storages_for(backend, env):
    """Monta STORAGES a partir de STORAGE_BACKEND e das variáveis AWS_* (env = dicionário de variáveis)."""
    if backend == 'local':
        return {'default': LOCAL, 'staticfiles': STATIC}
    if backend == 'cloudinary':
        if not env.get('CLOUDINARY_URL'):
            raise ImproperlyConfigured('Com STORAGE_BACKEND=cloudinary, defina CLOUDINARY_URL.')
        default = {
            'BACKEND': 'hubflow.core.storage.CloudinaryStorage',
            'OPTIONS': {'cloudinary_url': env['CLOUDINARY_URL']},
        }
        return {'default': default, 'staticfiles': STATIC}
    if backend != 's3':
        raise ImproperlyConfigured(f'STORAGE_BACKEND deve ser "local", "s3" ou "cloudinary", não "{backend}".')
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


@deconstructible
class CloudinaryStorage(Storage):
    """Arquivos no Cloudinary com a lib oficial, como "raw" (qualquer tipo, URL estável com a extensão).

    O Cloudinary acrescenta um sufixo único ao nome, então não há colisão nem consulta de existência.
    """

    resource_type = 'raw'

    def __init__(self, cloudinary_url):
        import cloudinary

        parsed = urlparse(cloudinary_url)  # cloudinary://API_KEY:API_SECRET@CLOUD_NAME
        cloudinary.config(cloud_name=parsed.hostname, api_key=parsed.username, api_secret=parsed.password, secure=True)
        self.cloud_name = parsed.hostname

    def _save(self, name, content):
        import cloudinary.uploader

        folder, filename = posixpath.split(name)
        content.seek(0)
        result = cloudinary.uploader.upload(
            content,
            folder=folder,
            filename_override=filename,
            use_filename=True,
            unique_filename=True,
            resource_type=self.resource_type,
        )
        return result['public_id']

    def get_available_name(self, name, max_length=None):
        return name  # o nome final vem do Cloudinary (com sufixo único)

    def exists(self, name):
        return False

    def url(self, name):
        from cloudinary.utils import cloudinary_url

        return cloudinary_url(name, resource_type=self.resource_type, secure=True)[0]

    def delete(self, name):
        import cloudinary.uploader

        cloudinary.uploader.destroy(name, resource_type=self.resource_type)

    def _open(self, name, mode='rb'):
        with urlopen(self.url(name)) as response:  # noqa: S310 (URL do próprio Cloudinary)
            return ContentFile(response.read(), name=name)
