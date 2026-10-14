from django.db import migrations


def backfill(apps, schema_editor):
    """Cards antigos ganham a sprint 1 do projeto (RN-61)."""
    Card = apps.get_model('boards', 'Card')
    Sprint = apps.get_model('sprints', 'Sprint')
    Project = apps.get_model('projects', 'Project')
    for project_id in Card.objects.filter(sprint__isnull=True).values_list('project_id', flat=True).distinct():
        sprint = Sprint.objects.filter(project_id=project_id, is_open=True).order_by('-number').first()
        if sprint is None:
            project = Project.objects.get(id=project_id)
            project.last_sprint_number += 1
            project.save(update_fields=['last_sprint_number'])
            sprint = Sprint.objects.create(project_id=project_id, number=project.last_sprint_number)
        Card.objects.filter(project_id=project_id, sprint__isnull=True).update(sprint=sprint)


class Migration(migrations.Migration):
    dependencies = [('boards', '0010_card_sprint')]

    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
