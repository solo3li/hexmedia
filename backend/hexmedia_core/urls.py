from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
import inngest.django
from ai_studio.api import api
from ai_studio.views import chat_home_view
from ai_studio.inngest_tasks import inngest_client, inngest_functions

urlpatterns = [
    path('admin/', admin.site.urls),
    inngest.django.serve(inngest_client, inngest_functions),
    path('api/', api.urls),
    path('', chat_home_view, name='chat_home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
