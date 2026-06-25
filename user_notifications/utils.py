"""
WHAT: Utility functions for sending notifications
WHY: Easy notification creation from any app
"""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import UserNotification, NotificationPreference


def notify_user(recipient, notification_type, title, message, actor=None, url='', data=None, send_email=True):
    """
    WHAT: Send notification to user (in-app + WebSocket)
    """
    
    # Create in-app notification
    notification = UserNotification.create_notification(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        actor=actor,
        url=url,
        data=data
    )
    
    # Check if user wants this notification
    try:
        prefs = recipient.notification_prefs
        type_map = {
            'like': prefs.push_likes,
            'comment': prefs.push_comments,
            'follow': prefs.push_follows,
            'job_status': prefs.push_job_updates,
            'webinar_reminder': prefs.push_webinar_reminders,
            'group_invite': prefs.push_group_activity,
        }
        should_send = type_map.get(notification_type, True)
        
        if not should_send:
            return notification
    except NotificationPreference.DoesNotExist:
        pass
    
    # Send via WebSocket
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'notifications_{recipient.id}',
            {
                'type': 'send_notification',
                'notification': {
                    'id': notification.id,
                    'type': notification_type,
                    'title': title,
                    'message': message,
                    'actor': actor.username if actor else None,
                    'actor_name': actor.get_full_name() if actor else None,
                    'url': url,
                    'created_at': notification.created_at.isoformat(),
                }
            }
        )
    except Exception as e:
        print(f"WebSocket error: {e}")
    
    return notification