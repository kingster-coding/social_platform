"""
WHAT: Admin configuration for user_notifications app
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import UserNotification, NotificationPreference


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'recipient', 'notification_type', 'title_preview',
        'is_read', 'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'is_emailed', 'created_at']
    search_fields = ['recipient__username', 'recipient__email', 'title', 'message']
    readonly_fields = ['created_at', 'read_at']
    
    fieldsets = (
        (None, {
            'fields': ('recipient', 'actor', 'notification_type')
        }),
        (_('Content'), {
            'fields': ('title', 'message', 'url', 'data')
        }),
        (_('Status'), {
            'fields': ('is_read', 'is_emailed', 'read_at')
        }),
        (_('Timestamp'), {
            'fields': ('created_at',)
        }),
    )
    
    def title_preview(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_preview.short_description = _('Title')


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'daily_digest', 'weekly_digest', 'updated_at']
    list_filter = ['daily_digest', 'weekly_digest', 'quiet_hours_enabled']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        (_('Email Preferences'), {
            'fields': (
                'email_likes', 'email_comments', 'email_follows',
                'email_job_updates', 'email_webinar_reminders', 'email_group_activity'
            )
        }),
        (_('Push Preferences'), {
            'fields': (
                'push_likes', 'push_comments', 'push_follows',
                'push_job_updates', 'push_webinar_reminders', 'push_group_activity'
            )
        }),
        (_('Digest Settings'), {
            'fields': ('daily_digest', 'weekly_digest')
        }),
        (_('Quiet Hours'), {
            'fields': ('quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end')
        }),
        (_('Timestamp'), {
            'fields': ('updated_at',)
        }),
    )