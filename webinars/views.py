"""
WHAT: Webinars app views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count, Avg
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import (
    Webinar, WebinarCategory, WebinarRegistration,
    WebinarSession, WebinarQuestion, WebinarRating, WebinarCertificate
)
from .forms import (
    WebinarForm, WebinarRegistrationForm, QuestionForm,
    RatingForm, WebinarSearchForm
)


def webinar_list(request):
    """
    WHAT: List all webinars
    """
    
    webinars = Webinar.objects.filter(
        status__in=['scheduled', 'live']
    ).select_related('host', 'category')
    
    form = WebinarSearchForm(request.GET)
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        access_type = form.cleaned_data.get('access_type')
        
        if query:
            webinars = webinars.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__icontains=query) |
                Q(host__username__icontains=query)
            ).distinct()
        
        if category:
            webinars = webinars.filter(category_id=category)
        
        if access_type:
            webinars = webinars.filter(access_type=access_type)
    
    # Separate upcoming and live
    upcoming = webinars.filter(status='scheduled', scheduled_at__gt=timezone.now())
    live = webinars.filter(status='live')
    past = Webinar.objects.filter(status='ended').order_by('-scheduled_at')[:10]
    
    categories = WebinarCategory.objects.annotate(webinar_count=Count('webinars'))
    
    context = {
        'upcoming_webinars': upcoming[:20],
        'live_webinars': live[:5],
        'past_webinars': past,
        'categories': categories,
        'search_form': form,
    }
    
    return render(request, 'webinars/list.html', context)


def webinar_detail(request, slug):
    """
    WHAT: View webinar details
    """
    
    webinar = get_object_or_404(
        Webinar.objects.select_related('host', 'category'),
        slug=slug
    )
    
    webinar.increment_view()
    
    is_registered = False
    registration = None
    
    if request.user.is_authenticated:
        registration = WebinarRegistration.objects.filter(
            webinar=webinar, user=request.user
        ).first()
        is_registered = registration is not None
    
    # Get questions
    questions = webinar.questions.filter(is_answered=False).order_by('-upvotes')[:20]
    
    # Get ratings
    ratings = webinar.ratings.select_related('user').order_by('-created_at')[:10]
    avg_rating = webinar.ratings.aggregate(avg=Avg('rating'))['avg'] or 0
    
    context = {
        'webinar': webinar,
        'is_registered': is_registered,
        'registration': registration,
        'questions': questions,
        'ratings': ratings,
        'avg_rating': avg_rating,
        'spots_left': webinar.spots_left,
    }
    
    return render(request, 'webinars/detail.html', context)


@login_required
def create_webinar(request):
    """
    WHAT: Create a new webinar (host only)
    """
    
    if request.method == 'POST':
        form = WebinarForm(request.POST, request.FILES)
        if form.is_valid():
            webinar = form.save(commit=False)
            webinar.host = request.user
            webinar.status = 'scheduled'
            webinar.save()
            messages.success(request, _('Webinar created successfully!'))
            return redirect('webinars:detail', slug=webinar.slug)
    else:
        form = WebinarForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'webinars/create.html', context)


@login_required
def register_webinar(request, slug):
    """
    WHAT: Register for a webinar
    """
    
    webinar = get_object_or_404(Webinar, slug=slug)
    
    # Check if registration is open
    if not webinar.registration_open:
        messages.error(request, _('Registration is closed for this webinar.'))
        return redirect('webinars:detail', slug=slug)
    
    # Check if full
    if webinar.is_full:
        messages.error(request, _('This webinar is full.'))
        return redirect('webinars:detail', slug=slug)
    
    # Check if already registered
    if WebinarRegistration.objects.filter(webinar=webinar, user=request.user).exists():
        messages.warning(request, _('You are already registered for this webinar.'))
        return redirect('webinars:detail', slug=slug)
    
    if request.method == 'POST':
        form = WebinarRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.webinar = webinar
            registration.user = request.user
            registration.email = request.user.email
            
            # Simulate payment check for paid webinars
            if webinar.access_type == 'paid':
                registration.payment_status = 'completed'
                registration.payment_id = 'pay_webinar_mock_' + timezone.now().strftime('%Y%m%d%H%M%S')
                registration.amount_paid = webinar.price

            registration.save()
            
            # Send real-time notification to host
            from django.urls import reverse
            from user_notifications.utils import notify_user
            
            webinar_url = reverse('webinars:detail', kwargs={'slug': webinar.slug})
            notify_user(
                recipient=webinar.host,
                notification_type='webinar_reminder',
                title='New Webinar Registration',
                message=f'{request.user.get_full_name() or request.user.username} registered for your webinar: {webinar.title}',
                actor=request.user,
                url=webinar_url
            )
            
            messages.success(request, _('Successfully registered for the webinar!'))
            return redirect('webinars:registration_success', registration_id=registration.id)
    else:
        form = WebinarRegistrationForm(initial={'email': request.user.email})
    
    context = {
        'webinar': webinar,
        'form': form,
    }
    
    return render(request, 'webinars/register.html', context)


@login_required
def registration_success(request, registration_id):
    """Registration confirmation page"""
    registration = get_object_or_404(WebinarRegistration, id=registration_id, user=request.user)
    return render(request, 'webinars/registration_success.html', {'registration': registration})


@login_required
def join_webinar(request, slug):
    """
    WHAT: Join live webinar room
    """
    
    webinar = get_object_or_404(Webinar, slug=slug)
    
    # Check if user is registered
    registration = WebinarRegistration.objects.filter(
        webinar=webinar, user=request.user
    ).first()
    
    if webinar.require_registration and not registration and request.user != webinar.host:
        messages.error(request, _('You must register to join this webinar.'))
        return redirect('webinars:detail', slug=slug)
    
    # Create session record
    session = WebinarSession.objects.create(
        webinar=webinar,
        user=request.user
    )
    
    # Mark as attended if registered
    if registration and registration.status == 'registered':
        registration.mark_attended()
        
        # Send real-time notification to host that attendee joined
        from django.urls import reverse
        from user_notifications.utils import notify_user
        
        if request.user != webinar.host:
            webinar_url = reverse('webinars:detail', kwargs={'slug': webinar.slug})
            notify_user(
                recipient=webinar.host,
                notification_type='webinar_reminder',
                title='Attendee Joined Webinar',
                message=f'{request.user.get_full_name() or request.user.username} has joined your live webinar: {webinar.title}',
                actor=request.user,
                url=webinar_url
            )
    
    # Update webinar status if first attendee
    if webinar.status == 'scheduled':
        webinar.status = 'live'
        webinar.started_at = timezone.now()
        webinar.save()
    
    context = {
        'webinar': webinar,
        'session': session,
        'jitsi_url': webinar.get_jitsi_url(),
        'is_host': request.user == webinar.host,
    }
    
    return render(request, 'webinars/room.html', context)


@login_required
@require_POST
def leave_webinar(request, session_id):
    """Record when user leaves webinar"""
    
    session = get_object_or_404(WebinarSession, id=session_id, user=request.user)
    session.left_at = timezone.now()
    session.duration_seconds = (session.left_at - session.joined_at).seconds
    session.save()
    
    return JsonResponse({'success': True})


@login_required
@require_POST
def ask_question(request, slug):
    """Ask a question during webinar"""
    
    webinar = get_object_or_404(Webinar, slug=slug)
    form = QuestionForm(request.POST)
    
    if form.is_valid():
        question = form.save(commit=False)
        question.webinar = webinar
        question.user = request.user
        question.save()
        
        if request.headers.get('HX-Request'):
            return render(request, 'webinars/partials/question.html', {'question': question})
        
        messages.success(request, _('Question submitted!'))
    
    return redirect('webinars:room', slug=slug)


@login_required
@require_POST
def upvote_question(request, question_id):
    """Upvote a question"""
    
    question = get_object_or_404(WebinarQuestion, id=question_id)
    question.upvotes += 1
    question.save()
    
    return JsonResponse({'upvotes': question.upvotes})


@login_required
@require_POST
def rate_webinar(request, slug):
    """Rate a webinar after attending"""
    
    webinar = get_object_or_404(Webinar, slug=slug)
    
    # Check if already rated
    if WebinarRating.objects.filter(webinar=webinar, user=request.user).exists():
        messages.warning(request, _('You have already rated this webinar.'))
        return redirect('webinars:detail', slug=slug)
    
    form = RatingForm(request.POST)
    if form.is_valid():
        rating = form.save(commit=False)
        rating.webinar = webinar
        rating.user = request.user
        rating.save()
        messages.success(request, _('Thank you for your rating!'))
    
    return redirect('webinars:detail', slug=slug)


@login_required
def my_webinars(request):
    """
    WHAT: User's registered and hosted webinars
    """
    
    registered = WebinarRegistration.objects.filter(
        user=request.user
    ).select_related('webinar').order_by('-registered_at')
    
    hosted = Webinar.objects.filter(host=request.user).order_by('-scheduled_at')
    
    context = {
        'registered_webinars': registered,
        'hosted_webinars': hosted,
    }
    
    return render(request, 'webinars/my_webinars.html', context)


@login_required
def host_dashboard(request):
    """
    WHAT: Dashboard for webinar hosts
    """
    
    hosted_webinars = Webinar.objects.filter(
        host=request.user
    ).annotate(
        reg_count=Count('registrations'),
        attended_count=Count('registrations', filter=Q(registrations__status='attended'))
    ).order_by('-scheduled_at')
    
    total_attendees = sum(w.attendance_count for w in hosted_webinars)
    total_registrations = sum(w.registration_count for w in hosted_webinars)
    total_revenue = sum(w.price * w.registration_count for w in hosted_webinars if w.access_type == 'paid')
    
    context = {
        'hosted_webinars': hosted_webinars[:20],
        'total_webinars': hosted_webinars.count(),
        'total_attendees': total_attendees,
        'total_registrations': total_registrations,
        'total_revenue': total_revenue,
    }
    
    return render(request, 'webinars/host_dashboard.html', context)