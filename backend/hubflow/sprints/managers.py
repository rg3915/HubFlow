from django.db import models


class SprintManager(models.Manager):
    def latest_open(self, project):
        return self.filter(project=project, is_open=True).order_by('-number').first()
