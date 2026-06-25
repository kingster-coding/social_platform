"""
WHAT: Reels app views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Reel, ReelLike, ReelComment, ReelShare, ReelSave
from .forms import ReelForm, ReelCommentForm
from feed.hashtag_utils import build_hashtag_lookup, extract_normalized_hashtags


@login_required
def reels_feed(request):
    """
    WHAT: Main reels feed - full screen vertical scroll
    WHY: Instagram-style reels browsing
    """
    
    # Get public reels (not drafts)
    reels = Reel.objects.filter(
        privacy='public',
        is_draft=False
    ).select_related('author').order_by('-created_at')[:50]
    
    context = {
        'reels': reels,
    }
    
    return render(request, 'reels/feed.html', context)


@login_required
def upload_reel(request):
    """
    WHAT: Upload new reel
    WHY: Content creation
    """
    
    if request.method == 'POST':
        form = ReelForm(request.POST, request.FILES)
        if form.is_valid():
            reel = form.save(commit=False)
            reel.author = request.user
            
            # Extract video duration (simplified - in production use library)
            # For now, set default 30 seconds
            reel.duration = 30
            
            # Check if draft or publish
            if 'publish' in request.POST:
                reel.is_draft = False
                messages.success(request, _('Reel published successfully!'))
            else:
                reel.is_draft = True
                messages.success(request, _('Reel saved as draft!'))
            
            reel.save()
            extract_hashtags_from_reel(reel)
            return redirect('reels:reel_detail', pk=reel.pk)
    else:
        form = ReelForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'reels/upload.html', context)


@login_required
def reel_detail(request, pk):
    """
    WHAT: Single reel detail page
    WHY: View reel with comments and actions
    """
    
    reel = get_object_or_404(
        Reel.objects.select_related('author'),
        pk=pk
    )
    
    # Increment view count
    reel.increment_view()
    
    # Get comments
    comments = reel.comments.select_related('user').all()[:50]  # type: ignore[attr-defined]
    
    # Check if user liked/saved
    user_liked = ReelLike.objects.filter(user=request.user, reel=reel).exists()
    user_saved = ReelSave.objects.filter(user=request.user, reel=reel).exists()
    
    # Get related reels
    related_reels = Reel.objects.filter(
        author=reel.author,
        is_draft=False
    ).exclude(pk=pk)[:10]
    
    comment_form = ReelCommentForm()
    
    context = {
        'reel': reel,
        'comments': comments,
        'user_liked': user_liked,
        'user_saved': user_saved,
        'related_reels': related_reels,
        'comment_form': comment_form,
    }
    
    return render(request, 'reels/detail.html', context)


@login_required
@require_POST
def like_reel(request, pk):
    """
    WHAT: Like/Unlike a reel
    """
    
    reel = get_object_or_404(Reel, pk=pk)
    
    like, created = ReelLike.objects.get_or_create(
        user=request.user,
        reel=reel
    )
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    if request.headers.get('HX-Request'):
        return HttpResponse(f'<span class="like-count">{reel.like_count}</span>')
    
    return redirect(request.META.get('HTTP_REFERER', 'reels:feed'))


@login_required
@require_POST
def save_reel(request, pk):
    """
    WHAT: Save/Unsave a reel
    """
    
    reel = get_object_or_404(Reel, pk=pk)
    
    saved, created = ReelSave.objects.get_or_create(
        user=request.user,
        reel=reel
    )
    
    if not created:
        saved.delete()
        messages.info(request, _('Reel removed from saved'))
    else:
        messages.success(request, _('Reel saved!'))
    
    if request.headers.get('HX-Request'):
        return HttpResponse('OK')
    
    return redirect(request.META.get('HTTP_REFERER', 'reels:feed'))


@login_required
@require_POST
def share_reel(request, pk):
    """
    WHAT: Share a reel
    """
    
    reel = get_object_or_404(Reel, pk=pk)
    
    ReelShare.objects.get_or_create(
        user=request.user,
        reel=reel
    )
    
    messages.success(request, _('Reel shared!'))
    
    if request.headers.get('HX-Request'):
        return HttpResponse(f'<span class="share-count">{reel.share_count}</span>')
    
    return redirect('reels:reel_detail', pk=pk)


@login_required
@require_POST
def add_comment(request, pk):
    """
    WHAT: Add comment to reel
    """
    
    reel = get_object_or_404(Reel, pk=pk)
    form = ReelCommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.reel = reel
        comment.save()
        messages.success(request, _('Comment added!'))
    
    return redirect('reels:reel_detail', pk=pk)


@login_required
def my_reels(request):
    """
    WHAT: User's own reels (including drafts)
    """
    
    reels = Reel.objects.filter(author=request.user).order_by('-created_at')
    
    context = {
        'reels': reels,
    }
    
    return render(request, 'reels/my_reels.html', context)


@login_required
def saved_reels(request):
    """
    WHAT: User's saved reels
    """
    
    saved = ReelSave.objects.filter(
        user=request.user
    ).select_related('reel', 'reel__author').order_by('-created_at')
    
    context = {
        'saved_reels': saved,
    }
    
    return render(request, 'reels/saved.html', context)


def extract_hashtags_from_reel(reel):
    from feed.models import Hashtag
    from feed.models import Post

    for tag_name in extract_normalized_hashtags(reel.caption):
        hashtag, _ = Hashtag.objects.get_or_create(name=tag_name)

        public_reel_count = Reel.objects.filter(
            privacy='public',
            is_draft=False,
        ).filter(build_hashtag_lookup('caption', tag_name)).count()

        public_post_count = Post.objects.filter(
            privacy='public'
        ).filter(
            Q(scheduled_at__isnull=True) | Q(scheduled_at__lte=timezone.now())
        ).filter(
            build_hashtag_lookup('content', tag_name)
        ).count()

        hashtag.post_count = public_post_count + public_reel_count
        hashtag.save(update_fields=['post_count'])
