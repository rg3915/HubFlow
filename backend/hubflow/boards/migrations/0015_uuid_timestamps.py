# Refactor #134: uuid7 em todos os models e created/modified (TimeStampedModel) no lugar de CreatedModel.
from django.db import migrations

from hubflow.core.migration_ops import add_created, add_modified, add_uuid


class Migration(migrations.Migration):
    dependencies = [('boards', '0014_card_issue')]

    operations = [
        add_created('label'),
        add_modified('label'),
        *add_uuid('boards', 'label'),
        *add_uuid('boards', 'card'),
        add_modified('cardmove'),
        *add_uuid('boards', 'cardmove'),
        *add_uuid('boards', 'comment'),
        add_created('checklistitem'),
        add_modified('checklistitem'),
        *add_uuid('boards', 'checklistitem'),
        add_modified('attachment'),
        *add_uuid('boards', 'attachment'),
        add_modified('cardevent'),
        *add_uuid('boards', 'cardevent'),
    ]
