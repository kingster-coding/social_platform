"""
URL configuration for core project.

Is file mein hum batate hain ki kaunsa URL kaunsa view dikhayega.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views  # Top pe add karo

urlpatterns = [
    path('', include('feed.urls')),  # ⭐ Feed app as home page
    path('reels/', include('reels.urls')),  # ⭐ YEH LINE ADD KARO
    path('research/', include('research.urls')),  # ⭐ YEH LINE ADD KARO
    path('jobs/', include('jobs.urls')),  # ⭐ YEH LINE ADD KARO
    path('webinars/', include('webinars.urls')),  # ⭐ YEH LINE ADD KARO
    path('groups/', include('groups.urls')),  # ⭐ YEH LINE ADD KARO
    path('chat/', include('chat.urls')),  # ⭐ ADD THIS
    path('notifications/', include('user_notifications.urls')),  # ⭐ ADD THIS
    path('search/', include('search_app.urls')),  # ⭐ ADD THIS
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),
    path('monetization/', include('monetization.urls')),
]

# Development mein media files serve karna (Production mein Nginx/S3 handle karega)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)