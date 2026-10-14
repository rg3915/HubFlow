import pytest
from django.core.exceptions import ImproperlyConfigured

from hubflow.core.storage import storages_for

ENV = {
    'AWS_STORAGE_BUCKET_NAME': 'hubflow',
    'AWS_S3_ENDPOINT_URL': 'http://s3:8333',
    'AWS_ACCESS_KEY_ID': 'chave',
    'AWS_SECRET_ACCESS_KEY': 'segredo',
}


def test_local_e_o_padrao():
    assert storages_for('local', {})['default']['BACKEND'] == 'django.core.files.storage.FileSystemStorage'


def test_s3_le_as_variaveis():
    default = storages_for('s3', ENV | {'AWS_S3_CUSTOM_DOMAIN': 'localhost:8333/hubflow'})['default']

    assert default['BACKEND'] == 'storages.backends.s3.S3Storage'
    assert (
        default['OPTIONS'].items()
        >= {
            'bucket_name': 'hubflow',
            'endpoint_url': 'http://s3:8333',
            'access_key': 'chave',
            'secret_key': 'segredo',
            'custom_domain': 'localhost:8333/hubflow',
            'file_overwrite': False,
        }.items()
    )


def test_s3_sem_bucket_avisa():
    with pytest.raises(ImproperlyConfigured, match='AWS_STORAGE_BUCKET_NAME'):
        storages_for('s3', {})


def test_backend_desconhecido_avisa():
    with pytest.raises(ImproperlyConfigured, match='STORAGE_BACKEND'):
        storages_for('ftp', {})


def test_s3_monta_a_url_do_arquivo():
    from django.core.files.storage import storages
    from django.test import override_settings

    public = {'AWS_S3_CUSTOM_DOMAIN': 'localhost:8333/hubflow', 'AWS_S3_URL_PROTOCOL': 'http:'}
    with override_settings(STORAGES=storages_for('s3', ENV | public)):
        storages._storages = {}  # descarta a instância já criada
        url = storages['default'].url('attachments/a.txt')
    storages._storages = {}

    assert url == 'http://localhost:8333/hubflow/attachments/a.txt'


CLOUDINARY = {'CLOUDINARY_URL': 'cloudinary://123456:segredo@hubflow-demo'}


def test_cloudinary_le_a_url_de_configuracao():
    default = storages_for('cloudinary', CLOUDINARY)['default']

    assert default == {
        'BACKEND': 'hubflow.core.storage.CloudinaryStorage',
        'OPTIONS': {'cloudinary_url': 'cloudinary://123456:segredo@hubflow-demo'},
    }


def test_cloudinary_sem_url_avisa():
    with pytest.raises(ImproperlyConfigured, match='CLOUDINARY_URL'):
        storages_for('cloudinary', {})


def test_cloudinary_envia_monta_url_e_apaga(monkeypatch):
    from django.core.files.base import ContentFile

    from hubflow.core.storage import CloudinaryStorage

    calls = {}

    def upload(file, **options):
        calls['upload'] = (file.read(), options)
        return {'public_id': 'attachments/2026/10/print_ab12cd.png'}

    monkeypatch.setattr('cloudinary.uploader.upload', upload)
    monkeypatch.setattr('cloudinary.uploader.destroy', lambda name, **o: calls.setdefault('destroy', (name, o)))
    storage = CloudinaryStorage(cloudinary_url=CLOUDINARY['CLOUDINARY_URL'])

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
