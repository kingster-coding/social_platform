"""
WHAT: Admin configuration for jobs app
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Company, JobCategory, Skill, Job, JobApplication, SavedJob, JobAlert


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'industry', 'size', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'industry', 'size']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('owner')


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'company', 'location', 'job_type', 
        'status', 'view_count', 'application_count', 'posted_at'
    ]
    list_filter = ['status', 'job_type', 'location_type', 'experience_level', 'category']
    search_fields = ['title', 'description', 'company__name', 'location']
    readonly_fields = ['view_count', 'application_count', 'created_at', 'updated_at']
    filter_horizontal = ['required_skills']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'company', 'category', 'status', 'is_featured')
        }),
        (_('Description'), {
            'fields': ('description', 'requirements', 'responsibilities', 'benefits')
        }),
        (_('Details'), {
            'fields': ('job_type', 'experience_level', 'location_type', 'location')
        }),
        (_('Skills'), {
            'fields': ('required_skills',)
        }),
        (_('Salary'), {
            'fields': ('salary_min', 'salary_max', 'salary_currency', 'salary_period', 'show_salary')
        }),
        (_('Application'), {
            'fields': ('application_deadline', 'vacancies', 'application_url')
        }),
        (_('Analytics'), {
            'fields': ('view_count', 'application_count')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'posted_at', 'expires_at')
        }),
    )


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'applicant_name', 'job', 'status', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['applicant_name', 'applicant_email', 'job__title', 'job__company__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('job', 'applicant', 'status')
        }),
        (_('Applicant Info'), {
            'fields': ('applicant_name', 'applicant_email', 'applicant_phone')
        }),
        (_('Application Materials'), {
            'fields': ('resume', 'cover_letter', 'additional_docs')
        }),
        (_('Internal'), {
            'fields': ('notes',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'job', 'created_at']


@admin.register(JobAlert)
class JobAlertAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'frequency', 'is_active', 'created_at']
    list_filter = ['frequency', 'is_active']