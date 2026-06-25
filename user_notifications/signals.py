"""
WHAT: Signals for user_notifications app
WHY: Auto-create preferences for new users
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import NotificationPreference

User = settings.AUTH_USER_MODEL


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Auto-create notification preferences for new users"""
    if created:
        NotificationPreference.objects.get_or_create(user=instance)