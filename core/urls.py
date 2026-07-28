from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from catalogo.views import ver_catalogo

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(('catalogo.urls', 'catalogo'), namespace='catalogo')),
    path('<slug:slug>/', ver_catalogo, name='catalogo'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)