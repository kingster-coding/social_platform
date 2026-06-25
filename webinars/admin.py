"""
WHAT: Admin configuration for webinars app
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    WebinarCategory, Webinar, WebinarRegistration,
    WebinarSession, WebinarQuestion, WebinarRating, WebinarCertificate
)


@admin.register(WebinarCategory)
class WebinarCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Webinar)
class WebinarAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'host', 'category', 'status', 'access_type',
        'scheduled_at', 'registration_count', 'attendance_count'
    ]
    list_filter = ['status', 'access_type', 'category', 'is_featured']
    search_fields = ['title', 'description', 'host__username', 'host__email']
    readonly_fields = [
        'view_count', 'registration_count', 'attendance_count',
        'created_at', 'updated_at', 'started_at', 'ended_at'
    ]
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        (None, {
            'fields': ('host', 'title', 'slug', 'description', 'status', 'is_featured')
        }),
        (_('Media'), {
            'fields': ('thumbnail', 'cover_image')
        }),
        (_('Categorization'), {
            'fields': ('category', 'tags')
        }),
        (_('Schedule'), {
            'fields': ('scheduled_at', 'duration_minutes', 'timezone')
        }),
        (_('Access'), {
            'fields': ('access_type', 'max_attendees', 'registration_deadline', 'price', 'currency')
        }),
        (_('Jitsi Integration'), {
            'fields': ('room_name', 'jitsi_server')
        }),
        (_('Features'), {
            'fields': ('enable_chat', 'enable_qa', 'enable_recording', 'auto_record', 
                      'require_registration', 'send_reminders')
        }),
        (_('Recording'), {
            'fields': ('recording_url', 'recording_duration')
        }),
        (_('Analytics'), {
            'fields': ('view_count', 'registration_count', 'attendance_count')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'started_at', 'ended_at')
        }),
    )


@admin.register(WebinarRegistration)
class WebinarRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        'registration_number', 'user', 'webinar', 'status',
        'payment_status', 'registered_at'
    ]
    list_filter = ['status', 'payment_status', 'registered_at']
    search_fields = ['registration_number', 'user__email', 'webinar__title']
    readonly_fields = ['registered_at', 'reminder_sent_at']


@admin.register(WebinarSession)
class WebinarSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'webinar', 'joined_at', 'duration_seconds']
    readonly_fields = ['joined_at']


@admin.register(WebinarQuestion)
class WebinarQuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'webinar', 'user', 'question_preview', 'is_answered', 'upvotes']
    list_filter = ['is_answered', 'is_pinned', 'created_at']
    search_fields = ['question', 'user__email']
    
    def question_preview(self, obj):
        return obj.question[:50]
    question_preview.short_description = _('Question')


@admin.register(WebinarRating)
class WebinarRatingAdmin(admin.ModelAdmin):
    list_display = ['id', 'webinar', 'user', 'rating', 'created_at']
    list_filter = ['rating']


@admin.register(WebinarCertificate)
class WebinarCertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'registration', 'issued_at']
    search_fields = ['certificate_number', 'registration__user__email']
    readonly_fields = ['issued_at']