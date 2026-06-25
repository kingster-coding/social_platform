"""
WHAT: User Notifications app models
WHY: Real-time alerts for user activities
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

User = settings.AUTH_USER_MODEL


class UserNotification(models.Model):
    """
    WHAT: User notification model
    """
    
    NOTIFICATION_TYPES = [
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('follow', 'Follow'),
        ('friend_request', 'Friend Request'),
        ('friend_accept', 'Friend Request Accepted'),
        ('job_application', 'Job Application'),
        ('job_status', 'Job Status Update'),
        ('webinar_reminder', 'Webinar Reminder'),
        ('webinar_start', 'Webinar Starting'),
        ('group_invite', 'Group Invitation'),
        ('group_join', 'Group Join Request'),
        ('mention', 'Mention'),
        ('share', 'Share'),
        ('system', 'System Notification'),
    ]
    
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_notifications'
    )
    
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='triggered_notifications',
        null=True,
        blank=True
    )
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField(max_length=500)
    url = models.URLField(max_length=500, blank=True)
    data = models.JSONField(default=dict, blank=True)
    
    is_read = models.BooleanField(default=False)
    is_emailed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('user notification')
        verbose_name_plural = _('user notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.recipient.username} - {self.notification_type}"
    
    def mark_as_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])
    
    @classmethod
    def create_notification(cls, recipient, notification_type, title, message, actor=None, url='', data=None):
        return cls.objects.create(
            recipient=recipient,
            actor=actor,
            notification_type=notification_type,
            title=title,
            message=message,
            url=url,
            data=data or {}
        )


class NotificationPreference(models.Model):
    """
    WHAT: User notification preferences
    """
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='notification_prefs'
    )
    
    # Email preferences
    email_likes = models.BooleanField(default=True)
    email_comments = models.BooleanField(default=True)
    email_follows = models.BooleanField(default=True)
    email_job_updates = models.BooleanField(default=True)
    email_webinar_reminders = models.BooleanField(default=True)
    email_group_activity = models.BooleanField(default=True)
    
    # Push/In-app preferences
    push_likes = models.BooleanField(default=True)
    push_comments = models.BooleanField(default=True)
    push_follows = models.BooleanField(default=True)
    push_job_updates = models.BooleanField(default=True)
    push_webinar_reminders = models.BooleanField(default=True)
    push_group_activity = models.BooleanField(default=True)
    
    # Digest settings
    daily_digest = models.BooleanField(default=False)
    weekly_digest = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('notification preference')
        verbose_name_plural = _('notification preferences')
    
    def __str__(self):
        return f"Preferences for {self.user.username}"