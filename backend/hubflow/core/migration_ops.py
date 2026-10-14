"""Operações de migration reaproveitadas pelas apps (uuid e carimbos de tempo em tabelas com dados)."""

import uuid

from django.db import migrations, models
from django.utils import timezone


def add_uuid(app_label, model_name):
    """uuid nulo → preenche um uuid7 por linha → único e obrigatório (um default só repetiria o valor)."""

    def fill(apps, schema_editor):
        model = apps.get_model(app_label, model_name)
        rows = list(model.objects.filter(uuid__isnull=True).only('pk'))
        for row in rows:
            row.uuid = uuid.uuid7()
        model.objects.bulk_update(rows, ['uuid'], batch_size=500)

    return [
        migrations.AddField(model_name, 'uuid', models.UUIDField('uuid', null=True, editable=False)),
        migrations.RunPython(fill, migrations.RunPython.noop),
        migrations.AlterField(
            model_name, 'uuid', models.UUIDField('uuid', default=uuid.uuid7, unique=True, editable=False)
        ),
    ]


def add_created(model_name):
    return migrations.AddField(
        model_name,
        'created',
        models.DateTimeField('criado em', auto_now_add=True, default=timezone.now),
        preserve_default=False,
    )


def add_modified(model_name):
    return migrations.AddField(
        model_name,
        'modified',
        models.DateTimeField('modificado em', auto_now=True, default=timezone.now),
        preserve_default=False,
    )
