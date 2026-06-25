"""
WHAT: Admin configuration for reels app
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Reel, ReelLike, ReelComment, ReelShare, ReelSave


@admin.register(Reel)
class ReelAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'author', 'title_preview', 'duration_display',
        'view_count', 'like_count', 'is_published', 'created_at'
    ]
    list_filter = ['privacy', 'is_draft', 'allow_comments', 'created_at']
    search_fields = ['title', 'caption', 'author__username', 'audio_title']
    readonly_fields = ['view_count', 'like_count', 'comment_count', 'share_count', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('author', 'title', 'caption', 'privacy')
        }),
        (_('Media'), {
            'fields': ('video', 'thumbnail', 'duration')
        }),
        (_('Audio'), {
            'fields': ('audio_title', 'audio_artist')
        }),
        (_('Settings'), {
            'fields': ('is_draft', 'allow_comments', 'allow_duet')
        }),
        (_('Analytics'), {
            'fields': ('view_count', 'like_count', 'comment_count', 'share_count')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'published_at')
        }),
    )
    
    def title_preview(self, obj):
        if obj.title:
            return obj.title[:30] + '...' if len(obj.title) > 30 else obj.title
        return obj.caption[:30] + '...' if obj.caption else '-'
    title_preview.short_description = _('Title')
    
    def duration_display(self, obj):
        """Format duration as MM:SS"""
        minutes = obj.duration // 60
        seconds = obj.duration % 60
        return f"{minutes}:{seconds:02d}"
    duration_display.short_description = _('Duration')


@admin.register(ReelComment)
class ReelCommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'reel', 'content_preview', 'created_at']
    search_fields = ['content', 'user__username']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content


@admin.register(ReelLike)
class ReelLikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'reel', 'created_at']


@admin.register(ReelShare)
class ReelShareAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'reel', 'created_at']


@admin.register(ReelSave)
class ReelSaveAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'reel', 'created_at']