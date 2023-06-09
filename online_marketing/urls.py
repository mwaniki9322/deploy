from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView


urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('JsWDuvqgB8sQjUV7IEXM5A/', include('mpesa.urls')),
    path('spinwin/', include('spinwin.urls')),
    path('admin-c/', include('custom_admin.urls')),
    path('tasks/', include('tasks_feature.urls')),
    path('fw/', include('flutterwave.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
