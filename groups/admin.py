"""
WHAT: Admin configuration for groups app
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    GroupCategory, Group, GroupMember, GroupJoinRequest,
    GroupInvitation, GroupPost, GroupPostLike, GroupPostComment, GroupEvent
)


@admin.register(GroupCategory)
class GroupCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'creator', 'category', 'visibility',
        'member_count', 'post_count', 'is_active', 'created_at'
    ]
    list_filter = ['visibility', 'is_active', 'category', 'requires_approval']
    search_fields = ['name', 'description', 'creator__username']
    readonly_fields = ['member_count', 'post_count', 'view_count', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'description', 'creator', 'category', 'tags')
        }),
        (_('Media'), {
            'fields': ('cover_image', 'icon')
        }),
        (_('Privacy Settings'), {
            'fields': ('visibility', 'requires_approval', 'post_approval')
        }),
        (_('Member Settings'), {
            'fields': ('allow_member_posts', 'allow_member_invites', 'show_member_list')
        }),
        (_('Rules'), {
            'fields': ('rules',)
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_featured')
        }),
        (_('Analytics'), {
            'fields': ('member_count', 'post_count', 'view_count')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['group', 'user', 'role', 'is_banned', 'joined_at']
    list_filter = ['role', 'is_banned', 'joined_at']
    search_fields = ['group__name', 'user__username', 'user__email']


@admin.register(GroupJoinRequest)
class GroupJoinRequestAdmin(admin.ModelAdmin):
    list_display = ['group', 'user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['group__name', 'user__username']


@admin.register(GroupInvitation)
class GroupInvitationAdmin(admin.ModelAdmin):
    list_display = ['group', 'user', 'invited_by', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['group__name', 'user__username']


@admin.register(GroupPost)
class GroupPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'group', 'author', 'status', 'is_pinned', 'created_at']
    list_filter = ['status', 'is_pinned', 'is_announcement', 'created_at']
    search_fields = ['content', 'author__username', 'group__name']


@admin.register(GroupEvent)
class GroupEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'creator', 'start_at', 'end_at']
    list_filter = ['is_online', 'start_at']
    search_fields = ['title', 'description', 'group__name']