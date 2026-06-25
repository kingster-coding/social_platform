"""
WHAT: WebSocket URL routing for chat app
WHY: Map WebSocket URLs to consumers
"""

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:room_id>/', consumers.ChatConsumer.as_asgi()),
]