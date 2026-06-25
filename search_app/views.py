"""
WHAT: Global search views
WHY: Search across all content types
"""

from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from accounts.models import User
from feed.models import Post
from reels.models import Reel
from research.models import ResearchPaper
from jobs.models import Job
from groups.models import Group
from webinars.models import Webinar


@login_required
def global_search(request):
    """
    WHAT: Main search view - searches across all models
    """
    
    query = request.GET.get('q', '').strip()
    tab = request.GET.get('tab', 'all')  # all, people, posts, jobs, papers, groups
    
    context = {
        'query': query,
        'active_tab': tab,
    }
    
    if query:
        if tab == 'all':
            # Search across all models (limited results per type)
            context['users'] = search_users(query, request.user)[:5]
            context['posts'] = search_posts(query, request.user)[:5]
            context['jobs'] = search_jobs(query)[:5]
            context['papers'] = search_papers(query)[:5]
            context['groups'] = search_groups(query)[:5]
            context['webinars'] = search_webinars(query)[:5]
            
        elif tab == 'people':
            results = search_users(query, request.user)
            context['users'] = paginate_results(request, results, 20)
            
        elif tab == 'posts':
            results = search_posts(query, request.user)
            context['posts'] = paginate_results(request, results, 20)
            
        elif tab == 'jobs':
            results = search_jobs(query)
            context['jobs'] = paginate_results(request, results, 20)
            
        elif tab == 'papers':
            results = search_papers(query)
            context['papers'] = paginate_results(request, results, 20)
            
        elif tab == 'groups':
            results = search_groups(query)
            context['groups'] = paginate_results(request, results, 20)
            
        elif tab == 'webinars':
            results = search_webinars(query)
            context['webinars'] = paginate_results(request, results, 20)
        
        # Calculate total counts for tabs
        context['total_users'] = search_users(query, request.user).count()
        context['total_posts'] = search_posts(query, request.user).count()
        context['total_jobs'] = search_jobs(query).count()
        context['total_papers'] = search_papers(query).count()
        context['total_groups'] = search_groups(query).count()
        context['total_webinars'] = search_webinars(query).count()
    
    return render(request, 'search_app/results.html', context)


def search_users(query, current_user):
    """Search users by name, username, email"""
    return User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(id=current_user.id).distinct().order_by('username')


def search_posts(query, user):
    """Search posts by content"""
    from feed.models import Post
    return Post.objects.filter(
        Q(content__icontains=query) &
        Q(privacy='public')
    ).select_related('author').order_by('-created_at')


def search_reels(query):
    """Search reels by title/caption"""
    from reels.models import Reel
    return Reel.objects.filter(
        Q(title__icontains=query) |
        Q(caption__icontains=query)
    ).filter(privacy='public', is_draft=False).select_related('author').order_by('-created_at')


def search_papers(query):
    """Search research papers"""
    from research.models import ResearchPaper
    return ResearchPaper.objects.filter(
        Q(title__icontains=query) |
        Q(abstract__icontains=query) |
        Q(keywords__icontains=query) |
        Q(primary_author__username__icontains=query)
    ).filter(status='published', access_level='public').select_related('primary_author').order_by('-created_at')


def search_jobs(query):
    """Search jobs"""
    from jobs.models import Job
    return Job.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(company__name__icontains=query) |
        Q(location__icontains=query)
    ).filter(status='active').select_related('company').order_by('-posted_at')


def search_groups(query):
    """Search groups"""
    from groups.models import Group
    return Group.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query) |
        Q(tags__icontains=query)
    ).filter(is_active=True, visibility__in=['public', 'private']).order_by('-member_count')


def search_webinars(query):
    """Search webinars"""
    from webinars.models import Webinar
    from django.utils import timezone
    return Webinar.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(tags__icontains=query)
    ).filter(status__in=['scheduled', 'live']).order_by('scheduled_at')


def paginate_results(request, queryset, per_page=20):
    """Helper to paginate results"""
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page', 1)
    return paginator.get_page(page)


@login_required
def quick_search(request):
    """
    WHAT: Quick search API for autocomplete/dropdown
    """
    from django.http import JsonResponse
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    # Users (top 3)
    users = search_users(query, request.user)[:3]
    for user in users:
        results.append({
            'type': 'user',
            'title': user.get_full_name() or user.username,
            'subtitle': f'@{user.username}',
            'url': f'/accounts/profile/{user.username}/',
            'icon': 'user'
        })
    
    # Posts (top 3)
    posts = search_posts(query, request.user)[:3]
    for post in posts:
        results.append({
            'type': 'post',
            'title': post.content[:50] + '...' if len(post.content) > 50 else post.content,
            'subtitle': f"By {post.author.username}",
            'url': f'/post/{post.id}/',
            'icon': 'post'
        })
    
    # Jobs (top 2)
    jobs = search_jobs(query)[:2]
    for job in jobs:
        results.append({
            'type': 'job',
            'title': job.title,
            'subtitle': job.company.name,
            'url': f'/jobs/job/{job.id}/',
            'icon': 'briefcase'
        })
    
    return JsonResponse({'results': results})