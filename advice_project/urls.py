"""
advice_project/urls.py
Main URL configuration for ADVICE platform (Django-only, no DRF).
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public pages
    path('', include('apps.institutions.urls')),

    # Authentication
    path('', include('apps.accounts.urls')),

    # Core platform
    path('', include('apps.counseling.urls')),
    path('', include('apps.messaging.urls')),
    path('', include('apps.progress.urls')),
    path('', include('apps.payments.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'apps.institutions.views.handler404'
handler500 = 'apps.institutions.views.handler500'
