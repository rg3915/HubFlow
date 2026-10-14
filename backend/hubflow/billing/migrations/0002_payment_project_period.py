import django.db.models.deletion
from django.db import migrations, models


def fill_project(apps, schema_editor):
    """Pagamentos existentes herdam o projeto da sprint."""
    Payment = apps.get_model('billing', 'Payment')
    for payment in Payment.objects.select_related('sprint').filter(project__isnull=True):
        payment.project_id = payment.sprint.project_id
        payment.save(update_fields=['project'])


class Migration(migrations.Migration):
    dependencies = [
        ('billing', '0001_initial'),
        ('projects', '0004_sprint'),
        ('sprints', '0002_core_abstracts'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='project',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='payments',
                to='projects.project',
                verbose_name='projeto',
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='sprint',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='payments',
                to='sprints.sprint',
                verbose_name='sprint',
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='period_start',
            field=models.DateField(blank=True, null=True, verbose_name='início do período'),
        ),
        migrations.AddField(
            model_name='payment',
            name='period_end',
            field=models.DateField(blank=True, null=True, verbose_name='fim do período'),
        ),
        migrations.RunPython(fill_project, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='payment',
            name='project',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='payments',
                to='projects.project',
                verbose_name='projeto',
            ),
        ),
    ]
