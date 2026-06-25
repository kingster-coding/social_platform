"""
WHAT: Feed app views
WHY: Posts display, create, like, comment functionality
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Post, Like, Comment, Share, SavedPost
from .forms import PostForm, CommentForm
from .hashtag_utils import build_hashtag_lookup, extract_normalized_hashtags
from user_notifications.utils import notify_user


@login_required
def feed(request):
    """
    WHAT: Main feed page - shows posts from followed users and public posts
    WHY: Home page of the platform
    """
    page = request.GET.get('page', 1)
    try:
        page = int(page)
    except ValueError:
        page = 1

    # Show public posts and posts by users we follow
    following_ids = list(request.user.following.values_list('id', flat=True))
    following_ids.append(request.user.id) # Include self posts

    posts_query = Post.objects.filter(
        Q(privacy='public') | Q(author_id__in=following_ids),
        scheduled_at__isnull=True
    ).select_related('author').prefetch_related('likes', 'comments')

    scheduled_posts = Post.objects.filter(
        Q(privacy='public') | Q(author_id__in=following_ids),
        scheduled_at__lte=timezone.now()
    ).select_related('author').prefetch_related('likes', 'comments')

    all_posts = (posts_query | scheduled_posts).distinct().order_by('-created_at')

    # Paginate
    posts_per_page = 5
    start = (page - 1) * posts_per_page
    end = start + posts_per_page
    page_posts = all_posts[start:end]
    has_more = all_posts[end:end+1].exists()

    # Active stories
    from .models import Story
    active_stories = Story.objects.filter(
        created_at__gte=timezone.now() - timezone.timedelta(hours=24)
    ).select_related('author').order_by('-created_at')

    # Deduplicate stories by author
    stories_by_author = {}
    for story in active_stories:
        if story.author_id not in stories_by_author:
            stories_by_author[story.author_id] = story
    unique_stories = list(stories_by_author.values())

    # Follow suggestions
    from accounts.models import User
    suggestions = User.objects.exclude(
        id=request.user.id
    ).exclude(
        id__in=following_ids
    ).order_by('?')[:4]

    form = PostForm()

    context = {
        'posts': page_posts,
        'form': form,
        'stories': unique_stories,
        'suggestions': suggestions,
        'page': page,
        'next_page': page + 1,
        'has_more': has_more,
    }

    if request.headers.get('HX-Request') and page > 1:
        return render(request, 'feed/partials/post_list.html', context)

    return render(request, 'feed/feed.html', context)


@login_required
@require_POST
def create_post(request):
    """
    WHAT: Create new post
    WHY: User can post content, images, videos
    """
    
    form = PostForm(request.POST, request.FILES)
    
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        
        # Input Sanitization to prevent XSS attacks
        import bleach
        post.content = bleach.clean(post.content, tags=[], strip=True)
        
        post.save()
        
        # Extract and save hashtags
        extract_hashtags(post)
        
        messages.success(request, _('Post created successfully!'))
    else:
        messages.error(request, _('Error creating post. Please check your input.'))
    
    return redirect('feed:feed')


@login_required
def post_detail(request, pk):
    """
    WHAT: Single post detail page with comments
    WHY: View post with all comments and replies
    """
    
    post = get_object_or_404(
        Post.objects.select_related('author').prefetch_related(
            'likes', 
            'comments__user',
            'comments__replies__user'
        ),
        pk=pk
    )
    
    # Increment view count
    post.view_count += 1
    post.save(update_fields=['view_count'])
    
    comment_form = CommentForm()
    
    # Check if user liked this post
    user_liked = post.likes.filter(user=request.user).exists()
    user_reaction = None
    if user_liked:
        like_obj = post.likes.filter(user=request.user).first()
        user_reaction = like_obj.reaction if like_obj else 'like'
    
    context = {
        'post': post,
        'comment_form': comment_form,
        'user_liked': user_liked,
        'user_reaction': user_reaction,
    }
    
    return render(request, 'feed/post_detail.html', context)


@login_required
@require_POST
def like_post(request, pk):
    """
    WHAT: Like/Unlike a post with reaction support (HTMX compatible)
    WHY: User engagement with posts
    """
    
    post = get_object_or_404(Post, pk=pk)
    reaction = request.POST.get('reaction', 'like')
    
    # Check if user already liked this post
    like_obj = Like.objects.filter(user=request.user, post=post).first()
    
    if like_obj:
        if like_obj.reaction == reaction:
            like_obj.delete()
            liked = False
        else:
            like_obj.reaction = reaction
            like_obj.save()
            liked = True
    else:
        Like.objects.create(user=request.user, post=post, reaction=reaction)
        liked = True
    
    if liked and post.author != request.user:
        notify_user(
            recipient=post.author,
            notification_type='like',
            title='New Reaction',
            message=f'{request.user.username} reacted {reaction} on your post.',
            actor=request.user,
            url=post.get_absolute_url()
        )
    
    # HTMX request ke liye partial HTML return karo
    if request.headers.get('HX-Request'):
        return HttpResponse(f'<span class="like-count">{post.total_likes}</span>')  # type: ignore
    
    # Regular POST request ke liye redirect
    return redirect(request.META.get('HTTP_REFERER', 'feed:feed'))


@login_required
@require_POST
def add_comment(request, pk):
    """
    WHAT: Add comment to a post
    WHY: Users can discuss posts
    """
    
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.post = post
        
        # Input Sanitization to prevent XSS attacks
        import bleach
        comment.content = bleach.clean(comment.content, tags=[], strip=True)
        
        comment.save()
        messages.success(request, _('Comment added!'))
        
        if comment.user != post.author:
            notify_user(
                recipient=post.author,
                notification_type='comment',
                title='New Comment',
                message=f'{request.user.username} commented: "{comment.content[:30]}..."',
                actor=request.user,
                url=post.get_absolute_url()
            )
    
    return redirect('feed:post_detail', pk=pk)


@login_required
@require_POST
def reply_comment(request, pk, comment_id):
    """
    WHAT: Reply to a comment
    WHY: Nested comments/replies support
    """
    
    post = get_object_or_404(Post, pk=pk)
    parent_comment = get_object_or_404(Comment, pk=comment_id, post=post)
    
    form = CommentForm(request.POST)
    
    if form.is_valid():
        reply = form.save(commit=False)
        reply.user = request.user
        reply.post = post
        reply.parent = parent_comment
        
        # Input Sanitization to prevent XSS attacks
        import bleach
        reply.content = bleach.clean(reply.content, tags=[], strip=True)
        
        reply.save()
        messages.success(request, _('Reply added!'))
        
        if reply.user != parent_comment.user:
            notify_user(
                recipient=parent_comment.user,
                notification_type='comment',
                title='New Reply',
                message=f'{request.user.username} replied to your comment: "{reply.content[:30]}..."',
                actor=request.user,
                url=post.get_absolute_url()
            )
    
    return redirect('feed:post_detail', pk=pk)


@login_required
@require_POST
def share_post(request, pk):
    """
    WHAT: Share a post
    WHY: Users can repost others' content
    """
    
    post = get_object_or_404(Post, pk=pk)
    caption = request.POST.get('caption', '')
    
    # Check if user already shared this post
    share, created = Share.objects.get_or_create(
        user=request.user,
        post=post,
        defaults={'caption': caption}
    )
    
    if created:
        messages.success(request, _('Post shared!'))
        if post.author != request.user:
            notify_user(
                recipient=post.author,
                notification_type='share',
                title='Post Shared',
                message=f'{request.user.username} shared your post.',
                actor=request.user,
                url=post.get_absolute_url()
            )
    else:
        messages.info(request, _('You already shared this post'))
    
    return redirect('feed:feed')


@login_required
@require_POST
def save_post(request, pk):
    """
    WHAT: Save/Bookmark a post
    WHY: Users can save posts for later
    """
    
    post = get_object_or_404(Post, pk=pk)
    
    saved, created = SavedPost.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'saved': created,
        })
    
    if created:
        messages.success(request, _('Post saved!'))
    else:
        # Remove from saved
        saved.delete()
        messages.info(request, _('Post removed from saved'))
    
    return redirect(request.META.get('HTTP_REFERER', 'feed:feed'))


@login_required
def saved_posts(request):
    """
    WHAT: Show user's saved posts
    WHY: Bookmarked posts collection
    """
    
    saved = SavedPost.objects.filter(
        user=request.user
    ).select_related('post', 'post__author')
    
    context = {
        'saved_posts': saved,
    }
    
    return render(request, 'feed/saved_posts.html', context)


def extract_hashtags(post):
    """
    WHAT: Extract #hashtags from post content and save to database
    WHY: Hashtag search and trending functionality
    """
    from reels.models import Reel
    from .models import Hashtag

    for tag_name in extract_normalized_hashtags(post.content):
        hashtag, _ = Hashtag.objects.get_or_create(name=tag_name)

        public_post_count = Post.objects.filter(
            privacy='public',
            scheduled_at__isnull=True,
        ).filter(build_hashtag_lookup('content', tag_name)).count()

        published_scheduled_post_count = Post.objects.filter(
            privacy='public',
            scheduled_at__lte=timezone.now(),
        ).filter(build_hashtag_lookup('content', tag_name)).count()

        public_reel_count = Reel.objects.filter(
            privacy='public',
            is_draft=False,
        ).filter(build_hashtag_lookup('caption', tag_name)).count()

        hashtag.post_count = (
            public_post_count
            + published_scheduled_post_count
            + public_reel_count
        )
        hashtag.save(update_fields=['post_count'])


def hashtag_posts(request, tag):
    """
    WHAT: Show all posts with a specific hashtag
    """
    from reels.models import Reel
    from .models import Hashtag

    normalized_tag = tag.lower()
    hashtag = get_object_or_404(Hashtag, name=normalized_tag)

    posts = Post.objects.filter(
        privacy='public'
    ).filter(
        Q(scheduled_at__isnull=True) | Q(scheduled_at__lte=timezone.now())
    ).filter(
        build_hashtag_lookup('content', normalized_tag)
    ).select_related('author').order_by('-created_at')[:50]

    reels = Reel.objects.filter(
        privacy='public',
        is_draft=False,
    ).filter(
        build_hashtag_lookup('caption', normalized_tag)
    ).select_related('author').order_by('-created_at')[:50]

    hashtag.post_count = posts.count() + reels.count()
    hashtag.save(update_fields=['post_count'])

    context = {
        'hashtag': hashtag,
        'posts': posts,
        'reels': reels,
    }

    return render(request, 'feed/hashtag.html', context)


def trending_hashtags(request):
    """
    WHAT: API for trending hashtags
    """
    from django.http import JsonResponse
    from .models import Hashtag
    
    trending = Hashtag.objects.order_by('-post_count')[:10]
    
    data = []
    for tag in trending:
        data.append({
            'name': tag.name,
            'count': tag.post_count,
            'url': f'/hashtag/{tag.name}/'
        })
    
    return JsonResponse({'trending': data})


@login_required
@require_POST
def create_story(request):
    """
    WHAT: Create new story (24h expiry)
    """
    from .models import Story
    image = request.FILES.get('image')
    video = request.FILES.get('video')
    
    if image or video:
        Story.objects.create(
            author=request.user,
            image=image,
            video=video
        )
        messages.success(request, _('Story shared successfully!'))
    else:
        messages.error(request, _('Please select an image or video for your story.'))
        
    return redirect('feed:feed')
