"""
WHAT: URL patterns for jobs app
"""

from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='job_list'),
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    path('job/<int:pk>/apply/', views.apply_job, name='apply'),
    path('job/<int:pk>/save/', views.save_job, name='save'),
    path('post/', views.post_job, name='post_job'),
    path('post/<int:company_id>/', views.post_job, name='post_job_company'),
    path('company/create/', views.create_company, name='create_company'),
    path('applications/', views.my_applications, name='my_applications'),
    path('applications/<int:pk>/success/', views.application_success, name='application_success'),
    path('manage/<int:job_id>/applications/', views.manage_applications, name='manage_applications'),
    path('application/<int:app_id>/status/', views.update_application_status, name='update_status'),
    path('saved/', views.saved_jobs, name='saved_jobs'),
    path('recommended/', views.recommended_jobs, name='recommended'),
]