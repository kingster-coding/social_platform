"""
WHAT: Admin panel configuration for User and Profile models
WHY: Admin panel mein users ko manage karne ke liye
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Profile

# ============================================
# CUSTOM USER ADMIN
# ============================================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    WHAT: Custom User admin configuration
    WHY: Humare custom fields (bio, avatar, etc.) admin mein dikhane ke liye
    """
    
    # Fields to display in the list view
    list_display = [
        'email', 'username', 'get_full_name', 
        'is_active', 'is_staff', 'email_verified', 
        'date_joined', 'last_login'
    ]
    
    list_filter = [
        'is_active', 'is_staff', 'is_superuser', 
        'email_verified', 'is_private', 'date_joined'
    ]
    
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    # Fieldsets organize the admin form
    fieldsets = (
        # First section: Login credentials
        (None, {'fields': ('email', 'username', 'password')}),
        
        # Personal info section
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'bio', 
                'location', 'website', 'birth_date',
                'avatar', 'cover_photo'
            )
        }),
        
        # Permissions section
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'is_private', 'email_verified',
                'groups', 'user_permissions'
            )
        }),
        
        # Important dates section
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )
    
    # Fields when adding a new user via admin
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 
                'password1', 'password2',
                'first_name', 'last_name'
            ),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']
    
    def get_full_name(self, obj):
        """Custom method to display full name"""
        return obj.get_full_name()
    get_full_name.short_description = _('Full name')


# ============================================
# PROFILE ADMIN
# ============================================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    WHAT: Profile admin configuration
    """
    
    list_display = [
        'user', 'pronouns', 'gender', 
        'phone', 'profile_views', 'show_email'
    ]
    
    list_filter = ['gender', 'show_email', 'show_birth_date']
    search_fields = ['user__email', 'user__username', 'phone']
    
    fieldsets = (
        (None, {'fields': ('user',)}),
        (_('Personal Info'), {
            'fields': ('pronouns', 'gender', 'phone')
        }),
        (_('Social Links'), {
            'fields': ('linkedin', 'twitter', 'github', 'instagram')
        }),
        (_('Privacy Settings'), {
            'fields': ('show_email', 'show_birth_date')
        }),
        (_('Analytics'), {
            'fields': ('profile_views',)
        }),
    )
    
    readonly_fields = ['profile_views']