# Refactor #134: uuid7 em todos os models e created/modified (TimeStampedModel) no lugar de CreatedModel.
from django.db import migrations, models

from hubflow.core.migration_ops import add_modified, add_uuid


class Migration(migrations.Migration):
    dependencies = [('accounts', '0005_token_is_cli')]

    operations = [
        migrations.RenameField('user', 'date_joined', 'created'),
        migrations.AlterField('user', 'created', models.DateTimeField('criado em', auto_now_add=True)),
        add_modified('user'),
        *add_uuid('accounts', 'user'),
        add_modified('token'),
        *add_uuid('accounts', 'token'),
    ]
