"""
WHAT: Groups app views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from .models import (
    Group, GroupCategory, GroupMember, GroupJoinRequest,
    GroupInvitation, GroupPost, GroupPostLike, GroupPostComment, GroupEvent
)
from .forms import (
    GroupForm, GroupPostForm, JoinRequestForm,
    InvitationForm, GroupEventForm, GroupSearchForm
)


def group_list(request):
    """
    WHAT: List all discoverable groups
    """
    
    groups = Group.objects.filter(
        is_active=True,
        visibility__in=['public', 'private']
    ).select_related('creator', 'category')
    
    form = GroupSearchForm(request.GET)
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        
        if query:
            groups = groups.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query)
            ).distinct()
        
        if category:
            groups = groups.filter(category_id=category)
    
    # User's groups
    my_groups = []
    if request.user.is_authenticated:
        my_groups = Group.objects.filter(
            members__user=request.user,
            members__is_banned=False
        )[:10]
    
    categories = GroupCategory.objects.annotate(group_count=Count('groups'))
    
    context = {
        'groups': groups[:50],
        'my_groups': my_groups,
        'categories': categories,
        'search_form': form,
    }
    
    return render(request, 'groups/list.html', context)


def group_detail(request, slug):
    """
    WHAT: View group details and feed
    """
    
    group = get_object_or_404(
        Group.objects.select_related('creator', 'category'),
        slug=slug,
        is_active=True
    )
    
    # Check visibility
    if group.is_secret and not group.is_member(request.user):
        messages.error(request, _('This group is secret.'))
        return redirect('groups:list')
    
    is_member = group.is_member(request.user)
    is_moderator = group.is_moderator(request.user) if is_member else False
    has_pending_request = False
    
    if request.user.is_authenticated and not is_member:
        has_pending_request = GroupJoinRequest.objects.filter(
            group=group, user=request.user, status='pending'
        ).exists()
    
    # Get posts
    if is_member or group.is_public:
        posts = group.posts.filter(
            status='approved'
        ).select_related('author').order_by('-is_pinned', '-created_at')[:30]
    else:
        posts = []
    
    # Get members
    members = group.members.filter(is_banned=False).select_related('user')[:20]
    
    # Get pending requests (for moderators)
    pending_requests = []
    if is_moderator:
        pending_requests = group.join_requests.filter(status='pending').select_related('user')
    
    context = {
        'group': group,
        'is_member': is_member,
        'is_moderator': is_moderator,
        'has_pending_request': has_pending_request,
        'posts': posts,
        'members': members,
        'pending_requests': pending_requests,
        'post_form': GroupPostForm() if is_member else None,
    }
    
    return render(request, 'groups/detail.html', context)


@login_required
def create_group(request):
    """
    WHAT: Create a new group
    """
    
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            messages.success(request, _('Group created successfully!'))
            return redirect('groups:detail', slug=group.slug)
    else:
        form = GroupForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'groups/create.html', context)


@login_required
@require_POST
def join_group(request, slug):
    """
    WHAT: Join a group (or request to join)
    """
    
    group = get_object_or_404(Group, slug=slug, is_active=True)
    
    # Check if already member
    if group.is_member(request.user):
        messages.warning(request, _('You are already a member of this group.'))
        return redirect('groups:detail', slug=slug)
    
    # Check if banned
    if GroupMember.objects.filter(group=group, user=request.user, is_banned=True).exists():
        messages.error(request, _('You are banned from this group.'))
        return redirect('groups:list')
    
    # If requires approval, create join request
    if group.requires_approval and not group.is_public:
        message = request.POST.get('message', '')
        GroupJoinRequest.objects.get_or_create(
            group=group,
            user=request.user,
            defaults={'message': message}
        )
        messages.success(request, _('Your request to join has been sent.'))
    else:
        # Direct join
        GroupMember.objects.create(
            group=group,
            user=request.user,
            role='member'
        )
        messages.success(request, _(f'Welcome to {group.name}!'))
    
    return redirect('groups:detail', slug=slug)


@login_required
@require_POST
def leave_group(request, slug):
    """
    WHAT: Leave a group
    """
    
    group = get_object_or_404(Group, slug=slug)
    
    membership = GroupMember.objects.filter(group=group, user=request.user).first()
    if membership:
        # Can't leave if you're the only admin
        if membership.role == 'admin':
            admin_count = group.members.filter(role='admin', is_banned=False).count()
            if admin_count <= 1:
                messages.error(request, _('You cannot leave as the only admin. Transfer ownership first.'))
                return redirect('groups:detail', slug=slug)
        
        membership.delete()
        messages.success(request, _('You have left the group.'))
    
    return redirect('groups:list')


@login_required
@require_POST
def create_post(request, slug):
    """
    WHAT: Create a post in group
    """
    
    group = get_object_or_404(Group, slug=slug)
    
    if not group.is_member(request.user):
        messages.error(request, _('You must be a member to post.'))
        return redirect('groups:detail', slug=slug)
    
    form = GroupPostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.group = group
        post.author = request.user
        
        # Auto-approve if no approval required or user is moderator
        if not group.post_approval or group.is_moderator(request.user):
            post.status = 'approved'
        else:
            post.status = 'pending'
        
        post.save()
        
        if post.status == 'approved':
            messages.success(request, _('Post published!'))
        else:
            messages.info(request, _('Post submitted for approval.'))
    
    return redirect('groups:detail', slug=slug)


@login_required
@require_POST
def like_post(request, post_id):
    """Like/Unlike a group post"""
    
    post = get_object_or_404(GroupPost, id=post_id)
    
    like, created = GroupPostLike.objects.get_or_create(
        post=post,
        user=request.user
    )
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'like_count': post.like_count
    })


@login_required
@require_POST
def approve_request(request, request_id):
    """Approve a join request"""
    
    join_request = get_object_or_404(GroupJoinRequest, id=request_id)
    group = join_request.group
    
    if not group.is_moderator(request.user):
        messages.error(request, _('You are not authorized.'))
        return redirect('groups:detail', slug=group.slug)
    
    join_request.approve(processed_by=request.user)
    messages.success(request, _(f'{join_request.user.username} has been approved.'))
    
    return redirect('groups:detail', slug=group.slug)


@login_required
@require_POST
def reject_request(request, request_id):
    """Reject a join request"""
    
    join_request = get_object_or_404(GroupJoinRequest, id=request_id)
    group = join_request.group
    
    if not group.is_moderator(request.user):
        messages.error(request, _('You are not authorized.'))
        return redirect('groups:detail', slug=group.slug)
    
    join_request.reject(processed_by=request.user)
    messages.info(request, _(f'Request from {join_request.user.username} rejected.'))
    
    return redirect('groups:detail', slug=group.slug)


@login_required
@require_POST
def approve_post(request, post_id):
    """Approve a pending post"""
    
    post = get_object_or_404(GroupPost, id=post_id)
    
    if not post.group.is_moderator(request.user):
        messages.error(request, _('You are not authorized.'))
        return redirect('groups:detail', slug=post.group.slug)
    
    post.approve(approved_by=request.user)
    messages.success(request, _('Post approved!'))
    
    return redirect('groups:detail', slug=post.group.slug)


@login_required
def members_list(request, slug):
    """View all group members"""
    
    group = get_object_or_404(Group, slug=slug)
    
    if not group.show_member_list and not group.is_member(request.user):
        messages.error(request, _('Member list is private.'))
        return redirect('groups:detail', slug=slug)
    
    members = group.members.filter(is_banned=False).select_related('user').order_by('-role', 'joined_at')
    
    context = {
        'group': group,
        'members': members,
        'is_moderator': group.is_moderator(request.user),
    }
    
    return render(request, 'groups/members.html', context)


@login_required
@require_POST
def change_role(request, slug, user_id):
    """Change member role (admin only)"""
    
    group = get_object_or_404(Group, slug=slug)
    
    if not group.is_admin(request.user):
        messages.error(request, _('Only admins can change roles.'))
        return redirect('groups:members', slug=slug)
    
    member = get_object_or_404(GroupMember, group=group, user_id=user_id)
    new_role = request.POST.get('role')
    
    if new_role in ['admin', 'moderator', 'member']:
        # Can't demote the last admin
        if member.role == 'admin' and new_role != 'admin':
            admin_count = group.members.filter(role='admin', is_banned=False).count()
            if admin_count <= 1:
                messages.error(request, _('Cannot remove the last admin.'))
                return redirect('groups:members', slug=slug)
        
        member.role = new_role
        member.save()
        messages.success(request, _(f'Role updated to {new_role}.'))
    
    return redirect('groups:members', slug=slug)


@login_required
@require_POST
def remove_member(request, slug, user_id):
    """Remove a member from group"""
    
    group = get_object_or_404(Group, slug=slug)
    
    if not group.is_moderator(request.user):
        messages.error(request, _('You are not authorized.'))
        return redirect('groups:members', slug=slug)
    
    # Can't remove the only admin
    member = get_object_or_404(GroupMember, group=group, user_id=user_id)
    if member.role == 'admin':
        admin_count = group.members.filter(role='admin', is_banned=False).count()
        if admin_count <= 1:
            messages.error(request, _('Cannot remove the last admin.'))
            return redirect('groups:members', slug=slug)
    
    member.delete()
    messages.success(request, _('Member removed.'))
    
    return redirect('groups:members', slug=slug)


@login_required
@require_POST
def ban_member(request, slug, user_id):
    """Ban a member from group"""
    
    group = get_object_or_404(Group, slug=slug)
    
    if not group.is_moderator(request.user):
        messages.error(request, _('You are not authorized.'))
        return redirect('groups:members', slug=slug)
    
    member = get_object_or_404(GroupMember, group=group, user_id=user_id)
    
    # Can't ban the only admin
    if member.role == 'admin':
        admin_count = group.members.filter(role='admin', is_banned=False).count()
        if admin_count <= 1:
            messages.error(request, _('Cannot ban the last admin.'))
            return redirect('groups:members', slug=slug)
    
    member.is_banned = True
    member.ban_reason = request.POST.get('reason', '')
    member.save()
    messages.success(request, _('Member banned.'))
    
    return redirect('groups:members', slug=slug)


@login_required
def my_groups(request):
    """User's groups"""
    
    memberships = GroupMember.objects.filter(
        user=request.user,
        is_banned=False
    ).select_related('group').order_by('-joined_at')
    
    context = {
        'memberships': memberships,
    }
    
    return render(request, 'groups/my_groups.html', context)


@login_required
def events_list(request, slug):
    """
    WHAT: List all upcoming events for a group
    """
    from django.utils import timezone as tz
    
    group = get_object_or_404(Group, slug=slug, is_active=True)
    
    if group.is_secret and not group.is_member(request.user):
        messages.error(request, _('This group is secret.'))
        return redirect('groups:list')
    
    is_member = group.is_member(request.user)
    is_moderator = group.is_moderator(request.user) if is_member else False
    
    upcoming_events = GroupEvent.objects.filter(
        group=group,
        end_at__gte=tz.now()
    ).order_by('start_at')
    
    past_events = GroupEvent.objects.filter(
        group=group,
        end_at__lt=tz.now()
    ).order_by('-start_at')[:10]
    
    event_form = GroupEventForm() if is_moderator else None
    
    context = {
        'group': group,
        'is_member': is_member,
        'is_moderator': is_moderator,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'event_form': event_form,
    }
    
    return render(request, 'groups/events.html', context)


@login_required
@require_POST
def create_event(request, slug):
    """
    WHAT: Create a new group event (moderators only)
    """
    group = get_object_or_404(Group, slug=slug, is_active=True)
    
    if not group.is_moderator(request.user):
        messages.error(request, _('Only moderators can create events.'))
        return redirect('groups:events', slug=slug)
    
    form = GroupEventForm(request.POST)
    if form.is_valid():
        event = form.save(commit=False)
        event.group = group
        event.creator = request.user
        event.save()
        messages.success(request, _('Event created successfully!'))
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
    
    return redirect('groups:events', slug=slug)