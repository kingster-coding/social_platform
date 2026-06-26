"""
WHAT: URL patterns for accounts app
WHY: Profile pages ke URLs define karne ke liye
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # ============================================
    # REGISTRATION — Custom 2-phase flow
    # ============================================
    path('register/', views.register_view, name='register'),
    path('register/send-otp/', views.register_send_otp, name='register_send_otp'),
    path('register/verify-otp/', views.register_verify_otp, name='register_verify_otp'),
    path('register/username-preview/', views.username_preview, name='username_preview'),

    # OTP Verification URLs (for existing login flow)
    path('verify/', views.verify_email_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),

    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/settings/', views.profile_settings, name='settings'),
    path('profile/<str:username>/', views.profile_view, name='profile_detail'),
    path('profile/<str:username>/follow/', views.follow_unfollow, name='follow_unfollow'),
    path('debug-email/', views.debug_email_view, name='debug_email'),
]