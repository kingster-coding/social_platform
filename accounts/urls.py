"""
WHAT: URL patterns for accounts app
WHY: Profile pages ke URLs define karne ke liye
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # OTP Verification URLs
    path('verify/', views.verify_email_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),

    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/settings/', views.profile_settings, name='settings'),
    path('profile/<str:username>/', views.profile_view, name='profile_detail'),
    path('profile/<str:username>/follow/', views.follow_unfollow, name='follow_unfollow'),
]