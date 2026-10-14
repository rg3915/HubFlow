"""Onde ficam os arquivos enviados (anexos e avatares): disco local (padrão), S3 (AWS ou compatível) ou Cloudinary."""

import posixpath
from urllib.parse import urlparse
from urllib.request import urlopen

from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

BACKENDS = {
    'local': 'django.core.files.storage.FileSystemStorage',
    's3': 'storages.backends.s3.S3Storage',  # lê os AWS_* do settings.py
    'cloudinary': 'hubflow.core.storage.CloudinaryStorage',  # lê CLOUDINARY_URL do settings.py
}


def storage_backend(name, bucket='', cloudinary_url=''):
    """Classe de storage para STORAGE_BACKEND, conferindo o que cada uma precisa (erro claro ao subir)."""
    if name not in BACKENDS:
        raise ImproperlyConfigured(f'STORAGE_BACKEND deve ser "local", "s3" ou "cloudinary", não "{name}".')
    if name == 's3' and not bucket:
        raise ImproperlyConfigured('Com STORAGE_BACKEND=s3, defina AWS_STORAGE_BUCKET_NAME.')
    if name == 'cloudinary' and not cloudinary_url:
        raise ImproperlyConfigured('Com STORAGE_BACKEND=cloudinary, defina CLOUDINARY_URL.')
    return BACKENDS[name]


@deconstructible
class CloudinaryStorage(Storage):
    """Arquivos no Cloudinary com a lib oficial, como "raw" (qualquer tipo, URL estável com a extensão).

    O Cloudinary acrescenta um sufixo único ao nome, então não há colisão nem consulta de existência.
    """

    resource_type = 'raw'

    def __init__(self):
        import cloudinary
        from django.conf import settings

        parsed = urlparse(settings.CLOUDINARY_URL)  # cloudinary://API_KEY:API_SECRET@CLOUD_NAME
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
