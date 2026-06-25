"""
WHAT: Admin configuration for feed app models
WHY: Admin panel se posts manage karne ke liye
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Post, Like, Comment, Share, SavedPost, Hashtag


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'author', 'content_preview', 'privacy',
        'total_likes', 'total_comments', 'created_at', 'is_published'
    ]
    list_filter = ['privacy', 'is_pinned', 'created_at', 'author']
    search_fields = ['content', 'author__username', 'author__email']
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('author', 'content', 'privacy')
        }),
        (_('Media'), {
            'fields': ('image', 'video')
        }),
        (_('Settings'), {
            'fields': ('is_pinned', 'allow_comments', 'scheduled_at')
        }),
        (_('Analytics'), {
            'fields': ('view_count', 'created_at', 'updated_at')
        }),
    )
    
    def content_preview(self, obj):
        """Show first 50 chars of content"""
        if obj.content:
            return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
        return '-'
    content_preview.short_description = _('Content')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post', 'content_preview', 'is_reply', 'created_at']
    list_filter = ['is_reported', 'created_at']
    search_fields = ['content', 'user__username', 'post__content']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = _('Content')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post', 'reaction', 'created_at']
    list_filter = ['reaction', 'created_at']


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post', 'caption_preview', 'created_at']
    
    def caption_preview(self, obj):
        if obj.caption:
            return obj.caption[:30] + '...' if len(obj.caption) > 30 else obj.caption
        return '-'
    caption_preview.short_description = _('Caption')


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post', 'created_at']


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ['name', 'post_count', 'created_at']
    search_fields = ['name']