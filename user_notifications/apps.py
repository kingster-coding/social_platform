"""
WHAT: App configuration for user_notifications
"""

from django.apps import AppConfig


class UserNotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_notifications'
    verbose_name = 'User Notifications'
    
    def ready(self):
        import user_notifications.signals