"""
WHAT: URL patterns for chat app
"""

from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list, name='list'),
    path('<int:room_id>/', views.chat_room, name='room'),
    path('start/<int:user_id>/', views.start_chat, name='start'),
]