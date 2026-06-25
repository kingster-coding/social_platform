"""
WHAT: URL patterns for user_notifications app
"""

from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list, name='list'),
    path('unread-count/', views.unread_count, name='unread_count'),
    path('recent/', views.get_recent_notifications, name='recent'),
    path('<int:notification_id>/read/', views.mark_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('preferences/', views.preferences, name='preferences'),
]