"""
WHAT: WebSocket consumer for real-time chat
WHY: Handle WebSocket connections, messages, typing indicators
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatRoom, Message, TypingIndicator


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WHAT: Handles WebSocket connections for chat
    """
    
    async def connect(self):
        """When user connects to WebSocket"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']
        
        # Reject if not authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user is participant
        is_participant = await self.is_participant()
        if not is_participant:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notify others that user is online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'username': self.user.username,
                'status': 'online'
            }
        )
    
    async def disconnect(self, close_code):
        """When user disconnects"""
        if hasattr(self, 'room_group_name'):
            # Notify others that user is offline
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'status': 'offline'
                }
            )
            
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        msg_type = data.get('type', 'message')
        
        if msg_type == 'message':
            message = data.get('message', '')
            
            # Save to database
            msg_obj = await self.save_message(message)
            
            # Broadcast to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.user.id,
                    'sender_name': self.user.get_full_name() or self.user.username,
                    'message_id': msg_obj.id,
                    'timestamp': msg_obj.created_at.isoformat(),
                }
            )
        
        elif msg_type == 'typing':
            is_typing = data.get('is_typing', False)
            await self.update_typing_status(is_typing)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': is_typing
                }
            )
        
        elif msg_type == 'read':
            message_id = data.get('message_id')
            await self.mark_as_read(message_id)
    
    async def chat_message(self, event):
        """Send message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp'],
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))
    
    async def user_status(self, event):
        """Send user online/offline status"""
        await self.send(text_data=json.dumps({
            'type': 'status',
            'user_id': event['user_id'],
            'username': event['username'],
            'status': event['status']
        }))
    
    @database_sync_to_async
    def is_participant(self):
        """Check if user is participant of this room"""
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return room.participants.filter(id=self.user.id).exists()
        except ChatRoom.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, message):
        """Save message to database"""
        room = ChatRoom.objects.get(id=self.room_id)
        return Message.objects.create(
            room=room,
            sender=self.user,
            content=message
        )
    
    @database_sync_to_async
    def update_typing_status(self, is_typing):
        """Update typing indicator in database"""
        room = ChatRoom.objects.get(id=self.room_id)
        TypingIndicator.objects.update_or_create(
            room=room,
            user=self.user,
            defaults={'is_typing': is_typing, 'updated_at': timezone.now()}
        )
    
    @database_sync_to_async
    def mark_as_read(self, message_id):
        """Mark message as read"""
        try:
            msg = Message.objects.get(id=message_id)
            if msg.sender != self.user:
                msg.is_read = True
                msg.save(update_fields=['is_read'])
        except Message.DoesNotExist:
            pass