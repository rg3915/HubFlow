import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.test import override_settings

from hubflow.core.storage import CloudinaryStorage, storage_backend

S3 = {
    'AWS_STORAGE_BUCKET_NAME': 'hubflow',
    'AWS_S3_ENDPOINT_URL': 'http://s3:8333',
    'AWS_ACCESS_KEY_ID': 'chave',
    'AWS_SECRET_ACCESS_KEY': 'segredo',
    'AWS_S3_CUSTOM_DOMAIN': 'localhost:8333/hubflow',
    'AWS_S3_URL_PROTOCOL': 'http:',
    'AWS_QUERYSTRING_AUTH': False,
    'AWS_S3_FILE_OVERWRITE': False,
}
CLOUDINARY_URL = 'cloudinary://123456:segredo@hubflow-demo'


def test_local_e_o_padrao():
    assert storage_backend('local') == 'django.core.files.storage.FileSystemStorage'


def test_s3_e_cloudinary():
    assert storage_backend('s3', bucket='hubflow') == 'storages.backends.s3.S3Storage'
    assert storage_backend('cloudinary', cloudinary_url=CLOUDINARY_URL) == 'hubflow.core.storage.CloudinaryStorage'


def test_s3_sem_bucket_avisa():
    with pytest.raises(ImproperlyConfigured, match='AWS_STORAGE_BUCKET_NAME'):
        storage_backend('s3')


def test_cloudinary_sem_url_avisa():
    with pytest.raises(ImproperlyConfigured, match='CLOUDINARY_URL'):
        storage_backend('cloudinary')


def test_backend_desconhecido_avisa():
    with pytest.raises(ImproperlyConfigured, match='STORAGE_BACKEND'):
        storage_backend('ftp')


def test_s3_le_os_aws_do_settings():
    from storages.backends.s3 import S3Storage

    with override_settings(**S3):
        storage = S3Storage()

    assert storage.bucket_name == 'hubflow' and storage.endpoint_url == 'http://s3:8333'
    assert storage.access_key == 'chave' and storage.querystring_auth is False and storage.file_overwrite is False
    assert storage.url('attachments/a.txt') == 'http://localhost:8333/hubflow/attachments/a.txt'


def test_cloudinary_le_a_url_do_settings_envia_monta_url_e_apaga(monkeypatch):
    calls = {}

    def upload(file, **options):
        calls['upload'] = (file.read(), options)
        return {'public_id': 'attachments/2026/10/print_ab12cd.png'}

    monkeypatch.setattr('cloudinary.uploader.upload', upload)
    monkeypatch.setattr('cloudinary.uploader.destroy', lambda name, **o: calls.setdefault('destroy', (name, o)))
    with override_settings(CLOUDINARY_URL=CLOUDINARY_URL):
        storage = CloudinaryStorage()

    name = storage.save('attachments/2026/10/print.png', ContentFile(b'png'))

    assert name == 'attachments/2026/10/print_ab12cd.png'
    content, options = calls['upload']
    assert content == b'png'
    assert options.items() >= {'folder': 'attachments/2026/10', 'resource_type': 'raw', 'use_filename': True}.items()
    assert (
        storage.url(name)
        == 'https://res.cloudinary.com/hubflow-demo/raw/upload/v1/attachments/2026/10/print_ab12cd.png'
    )
    storage.delete(name)
    assert calls['destroy'] == (name, {'resource_type': 'raw'})
