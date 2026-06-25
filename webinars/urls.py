"""
WHAT: URL patterns for webinars app
"""

from django.urls import path
from . import views

app_name = 'webinars'

urlpatterns = [
    path('', views.webinar_list, name='list'),
    path('create/', views.create_webinar, name='create'),
    path('my/', views.my_webinars, name='my_webinars'),
    path('dashboard/', views.host_dashboard, name='dashboard'),
    path('<slug:slug>/', views.webinar_detail, name='detail'),
    path('<slug:slug>/register/', views.register_webinar, name='register'),
    path('<slug:slug>/join/', views.join_webinar, name='join'),
    path('<slug:slug>/ask/', views.ask_question, name='ask'),
    path('<slug:slug>/rate/', views.rate_webinar, name='rate'),
    path('registration/<int:registration_id>/success/', views.registration_success, name='registration_success'),
    path('session/<int:session_id>/leave/', views.leave_webinar, name='leave'),
    path('question/<int:question_id>/upvote/', views.upvote_question, name='upvote'),
]