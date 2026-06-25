"""
WHAT: Admin configuration for research app
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    ResearchCategory, ResearchPaper, PaperComment, 
    PaperLike, PaperSave, ResearcherFollow
)


@admin.register(ResearchCategory)
class ResearchCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'paper_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    
    def paper_count(self, obj):
        return obj.papers.count()
    paper_count.short_description = _('Papers')


@admin.register(ResearchPaper)
class ResearchPaperAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'primary_author', 'category', 'status',
        'view_count', 'download_count', 'created_at'
    ]
    list_filter = ['status', 'access_level', 'category', 'created_at']
    search_fields = ['title', 'abstract', 'keywords', 'primary_author__username', 'doi']
    readonly_fields = ['view_count', 'download_count', 'citation_count', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'abstract', 'keywords')
        }),
        (_('Authors'), {
            'fields': ('primary_author', 'co_authors', 'additional_authors')
        }),
        (_('Files'), {
            'fields': ('file', 'cover_image')
        }),
        (_('Publication Info'), {
            'fields': ('doi', 'journal_name', 'publication_date', 'volume', 'issue', 'pages')
        }),
        (_('Categorization'), {
            'fields': ('category',)
        }),
        (_('Settings'), {
            'fields': ('access_level', 'status', 'allow_comments', 'allow_download')
        }),
        (_('Version Control'), {
            'fields': ('version', 'previous_version', 'version_notes')
        }),
        (_('Analytics'), {
            'fields': ('view_count', 'download_count', 'citation_count')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'published_at')
        }),
    )


@admin.register(PaperComment)
class PaperCommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'paper', 'is_review', 'created_at']
    list_filter = ['is_review', 'created_at']
    search_fields = ['content', 'user__username', 'paper__title']


@admin.register(PaperLike)
class PaperLikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'paper', 'created_at']


@admin.register(PaperSave)
class PaperSaveAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'paper', 'created_at']


@admin.register(ResearcherFollow)
class ResearcherFollowAdmin(admin.ModelAdmin):
    list_display = ['id', 'follower', 'researcher', 'created_at']