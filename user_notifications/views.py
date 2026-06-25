"""
WHAT: Notifications views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib import messages
from .models import UserNotification, NotificationPreference


@login_required
def notification_list(request):
    """Show all notifications"""
    
    notifications = UserNotification.objects.filter(
        recipient=request.user
    ).select_related('actor').order_by('-created_at')
    
    paginator = Paginator(notifications, 20)
    page = request.GET.get('page', 1)
    notifications = paginator.get_page(page)
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'user_notifications/list.html', context)


@login_required
def unread_count(request):
    """API: Get unread notification count"""
    
    count = UserNotification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({'count': count})


@login_required
def get_recent_notifications(request):
    """API: Get recent notifications for dropdown"""
    
    notifications = UserNotification.objects.filter(
        recipient=request.user
    ).select_related('actor').order_by('-created_at')[:5]
    
    data = []
    for n in notifications:
        data.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'url': n.url,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat(),
            'actor_name': n.actor.get_full_name() if n.actor else None,
        })
    
    return JsonResponse({'notifications': data})


@login_required
@require_POST
def mark_read(request, notification_id):
    """Mark single notification as read"""
    
    notification = get_object_or_404(
        UserNotification,
        id=notification_id,
        recipient=request.user
    )
    notification.mark_as_read()
    
    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications as read"""
    
    UserNotification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    return JsonResponse({'success': True})


@login_required
def preferences(request):
    """Notification preferences page"""
    
    prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Email preferences
        prefs.email_likes = request.POST.get('email_likes') == 'on'
        prefs.email_comments = request.POST.get('email_comments') == 'on'
        prefs.email_follows = request.POST.get('email_follows') == 'on'
        prefs.email_job_updates = request.POST.get('email_job_updates') == 'on'
        prefs.email_webinar_reminders = request.POST.get('email_webinar_reminders') == 'on'
        prefs.email_group_activity = request.POST.get('email_group_activity') == 'on'
        
        # Push preferences
        prefs.push_likes = request.POST.get('push_likes') == 'on'
        prefs.push_comments = request.POST.get('push_comments') == 'on'
        prefs.push_follows = request.POST.get('push_follows') == 'on'
        prefs.push_job_updates = request.POST.get('push_job_updates') == 'on'
        prefs.push_webinar_reminders = request.POST.get('push_webinar_reminders') == 'on'
        prefs.push_group_activity = request.POST.get('push_group_activity') == 'on'
        
        # Digest
        prefs.daily_digest = request.POST.get('daily_digest') == 'on'
        prefs.weekly_digest = request.POST.get('weekly_digest') == 'on'
        
        prefs.save()
        messages.success(request, 'Notification preferences updated!')
        return redirect('notifications:preferences')
    
    context = {
        'preferences': prefs,
    }
    
    return render(request, 'user_notifications/preferences.html', context)