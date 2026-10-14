from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from hubflow.api import api
from hubflow.integrations.webhooks import github_webhook, gitlab_webhook
from hubflow.realtime.sse import project_events

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/webhooks/github/<int:project_id>', github_webhook),
    path('api/webhooks/gitlab/<int:project_id>', gitlab_webhook),
    path('api/projects/<int:project_id>/events', project_events),
    path('api/', api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
