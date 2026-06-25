"""
WHAT: Chat app views
WHY: Display chat list and rooms
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import ChatRoom, Message


@login_required
def chat_list(request):
    """Show all user's chat rooms"""
    
    rooms = ChatRoom.objects.filter(
        participants=request.user,
        is_active=True
    ).prefetch_related('participants').order_by('-updated_at')
    
    # Add unread count and last message
    for room in rooms:
        room.unread_count = room.get_unread_count(request.user)
        room.last_message = room.get_last_message()
    
    context = {
        'rooms': rooms,
    }
    
    if request.GET.get('partial'):
        return render(request, 'chat/partials/chat_list_items.html', context)
        
    return render(request, 'chat/list.html', context)


@login_required
def chat_room(request, room_id):
    """Show single chat room"""
    
    room = get_object_or_404(
        ChatRoom.objects.prefetch_related('participants'),
        id=room_id,
        participants=request.user,
        is_active=True
    )
    
    # Get recent messages (last 50)
    messages = room.messages.select_related('sender').order_by('-created_at')[:50]
    messages = reversed(messages)  # Show oldest first
    
    # Mark unread messages as read
    room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    # Load all rooms for sidebar
    all_rooms = ChatRoom.objects.filter(
        participants=request.user,
        is_active=True
    ).prefetch_related('participants').order_by('-updated_at')
    for r in all_rooms:
        r.unread_count = r.get_unread_count(request.user)
        r.last_message = r.get_last_message()
    
    context = {
        'room': room,
        'messages': messages,
        'all_rooms': all_rooms,
    }
    
    return render(request, 'chat/room.html', context)


@login_required
def start_chat(request, user_id):
    """Start or get direct chat with another user"""
    
    from accounts.models import User
    other_user = get_object_or_404(User, id=user_id)
    
    # Can't chat with yourself
    if other_user == request.user:
        return redirect('chat:list')
    
    # Find existing direct chat room
    room = ChatRoom.objects.filter(
        room_type='direct',
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    # Create new room if doesn't exist
    if not room:
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=request.user
        )
        room.participants.add(request.user, other_user)
    
    return redirect('chat:room', room_id=room.id)