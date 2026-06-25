"""
WHAT: URL patterns for groups app
"""

from django.urls import path
from . import views

app_name = 'groups'

urlpatterns = [
    path('', views.group_list, name='list'),
    path('my/', views.my_groups, name='my_groups'),
    path('create/', views.create_group, name='create'),
    path('<slug:slug>/', views.group_detail, name='detail'),
    path('<slug:slug>/join/', views.join_group, name='join'),
    path('<slug:slug>/leave/', views.leave_group, name='leave'),
    path('<slug:slug>/post/', views.create_post, name='create_post'),
    path('<slug:slug>/members/', views.members_list, name='members'),
    path('<slug:slug>/members/<int:user_id>/role/', views.change_role, name='change_role'),
    path('<slug:slug>/members/<int:user_id>/remove/', views.remove_member, name='remove_member'),
    path('<slug:slug>/members/<int:user_id>/ban/', views.ban_member, name='ban_member'),
    path('<slug:slug>/events/', views.events_list, name='events'),
    path('<slug:slug>/events/create/', views.create_event, name='create_event'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('request/<int:request_id>/approve/', views.approve_request, name='approve_request'),
    path('request/<int:request_id>/reject/', views.reject_request, name='reject_request'),
    path('post/<int:post_id>/approve/', views.approve_post, name='approve_post'),
]