# Refactor #134: uuid7 em todos os models e created/modified (TimeStampedModel) no lugar de CreatedModel.
from django.db import migrations

from hubflow.core.migration_ops import add_uuid


class Migration(migrations.Migration):
    dependencies = [('billing', '0002_payment_project_period')]

    operations = [
        *add_uuid('billing', 'payment'),
    ]
