"""
WHAT: Research app views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, FileResponse, Http404
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from .models import (
    ResearchPaper, ResearchCategory, PaperComment,
    PaperLike, PaperSave, ResearcherFollow
)
from .forms import PaperUploadForm, PaperSearchForm, PaperCommentForm


def paper_list(request):
    """
    WHAT: List all research papers with search/filter
    """
    
    papers = ResearchPaper.objects.filter(
        status='published'
    ).select_related('primary_author', 'category')
    
    form = PaperSearchForm(request.GET)
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        sort_by = form.cleaned_data.get('sort_by') or '-created_at'
        
        if query:
            papers = papers.filter(
                Q(title__icontains=query) |
                Q(abstract__icontains=query) |
                Q(keywords__icontains=query) |
                Q(primary_author__username__icontains=query) |
                Q(primary_author__first_name__icontains=query) |
                Q(primary_author__last_name__icontains=query)
            ).distinct()
        
        if category:
            papers = papers.filter(category=category)
        
        if sort_by:
            papers = papers.order_by(sort_by)
    
    categories = ResearchCategory.objects.annotate(paper_count=Count('papers'))
    
    context = {
        'papers': papers[:50],
        'categories': categories,
        'search_form': form,
    }
    
    return render(request, 'research/paper_list.html', context)


@login_required
def upload_paper(request):
    """
    WHAT: Upload new research paper
    """
    
    if request.method == 'POST':
        form = PaperUploadForm(request.POST, request.FILES)
        if form.is_valid():
            paper = form.save(commit=False)
            paper.primary_author = request.user
            paper.save()
            form.save_m2m()  # Save co-authors
            
            messages.success(request, _('Paper uploaded successfully!'))
            return redirect('research:paper_detail', pk=paper.pk)
    else:
        form = PaperUploadForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'research/upload.html', context)


def paper_detail(request, pk):
    """
    WHAT: View paper details
    """
    
    paper = get_object_or_404(
        ResearchPaper.objects.select_related('primary_author', 'category'),
        pk=pk
    )
    
    # Check access
    if paper.access_level == 'private' and request.user != paper.primary_author:
        messages.error(request, _('This paper is private.'))
        return redirect('research:paper_list')
    
    if paper.access_level == 'registered' and not request.user.is_authenticated:
        messages.warning(request, _('Please login to view this paper.'))
        return redirect('account_login')
    
    # Increment view count
    paper.increment_view()
    
    # Get comments
    comments = paper.comments.select_related('user').all()
    
    # Check if user liked/saved
    user_liked = False
    user_saved = False
    is_following = False
    
    if request.user.is_authenticated:
        user_liked = PaperLike.objects.filter(user=request.user, paper=paper).exists()
        user_saved = PaperSave.objects.filter(user=request.user, paper=paper).exists()
        is_following = ResearcherFollow.objects.filter(
            follower=request.user, 
            researcher=paper.primary_author
        ).exists()
    
    comment_form = PaperCommentForm()
    
    # Related papers
    related_papers = ResearchPaper.objects.filter(
        category=paper.category,
        status='published'
    ).exclude(pk=pk)[:5]
    
    context = {
        'paper': paper,
        'comments': comments,
        'user_liked': user_liked,
        'user_saved': user_saved,
        'is_following': is_following,
        'comment_form': comment_form,
        'related_papers': related_papers,
    }
    
    return render(request, 'research/paper_detail.html', context)


@login_required
def download_paper(request, pk):
    """
    WHAT: Download paper file
    """
    
    paper = get_object_or_404(ResearchPaper, pk=pk)
    
    # Check download permission
    if not paper.allow_download:
        messages.error(request, _('Download not allowed for this paper.'))
        return redirect('research:paper_detail', pk=pk)
    
    # Increment download count
    paper.increment_download()
    
    # Serve file
    try:
        response = FileResponse(
            paper.file.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="{paper.title}.pdf"'
        return response
    except FileNotFoundError:
        raise Http404(_('File not found'))


@login_required
@require_POST
def like_paper(request, pk):
    """
    WHAT: Like/Unlike a paper
    """
    
    paper = get_object_or_404(ResearchPaper, pk=pk)
    
    like, created = PaperLike.objects.get_or_create(
        user=request.user,
        paper=paper
    )
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    if request.headers.get('HX-Request'):
        return HttpResponse(f'<span>{paper.likes.count()}</span>')
    
    return redirect('research:paper_detail', pk=pk)


@login_required
@require_POST
def save_paper(request, pk):
    """
    WHAT: Save/Unsave a paper
    """
    
    paper = get_object_or_404(ResearchPaper, pk=pk)
    
    saved, created = PaperSave.objects.get_or_create(
        user=request.user,
        paper=paper
    )
    
    if not created:
        saved.delete()
        messages.info(request, _('Paper removed from library'))
    else:
        messages.success(request, _('Paper saved to library'))
    
    return redirect('research:paper_detail', pk=pk)


@login_required
@require_POST
def add_comment(request, pk):
    """
    WHAT: Add comment/review to paper
    """
    
    paper = get_object_or_404(ResearchPaper, pk=pk)
    form = PaperCommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.paper = paper
        comment.save()
        messages.success(request, _('Comment added!'))
    
    return redirect('research:paper_detail', pk=pk)


@login_required
@require_POST
def follow_researcher(request, username):
    """
    WHAT: Follow/Unfollow a researcher
    """
    
    from accounts.models import User
    researcher = get_object_or_404(User, username=username)
    
    if researcher == request.user:
        messages.error(request, _('You cannot follow yourself.'))
        return redirect('research:paper_list')
    
    follow, created = ResearcherFollow.objects.get_or_create(
        follower=request.user,
        researcher=researcher
    )
    
    if not created:
        follow.delete()
        messages.info(request, _(f'Unfollowed {researcher.get_full_name()}'))
    else:
        messages.success(request, _(f'Following {researcher.get_full_name()}'))
    
    return redirect(request.META.get('HTTP_REFERER', 'research:paper_list'))


@login_required
def my_library(request):
    """
    WHAT: User's saved papers and uploads
    """
    
    my_papers = ResearchPaper.objects.filter(primary_author=request.user)
    saved_papers = PaperSave.objects.filter(user=request.user).select_related('paper')
    
    context = {
        'my_papers': my_papers,
        'saved_papers': saved_papers,
    }
    
    return render(request, 'research/library.html', context)