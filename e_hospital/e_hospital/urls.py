
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from .views import home

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('patient/', include('patient.urls', namespace='patient')),
    path('doctor/', include('doctor.urls', namespace='doctor')),
    path('admin-panel/', include(('admin_panel.urls'), namespace='admin_panel')),

]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )