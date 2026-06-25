"""
WHAT: Jobs app views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from .models import Company, Job, JobApplication, SavedJob, JobCategory, Skill
from .forms import CompanyForm, JobForm, JobSearchForm, JobApplicationForm, JobAlertForm


def job_list(request):
    """
    WHAT: List all jobs with search/filter
    """
    
    jobs = Job.objects.filter(
        status='active'
    ).select_related('company', 'category')
    
    form = JobSearchForm(request.GET)
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        location = form.cleaned_data.get('location')
        job_type = form.cleaned_data.get('job_type')
        experience_level = form.cleaned_data.get('experience_level')
        location_type = form.cleaned_data.get('location_type')
        
        if query:
            jobs = jobs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(company__name__icontains=query)
            ).distinct()
        
        if location:
            jobs = jobs.filter(location__icontains=location)
        
        if job_type:
            jobs = jobs.filter(job_type=job_type)
        
        if experience_level:
            jobs = jobs.filter(experience_level=experience_level)
        
        if location_type:
            jobs = jobs.filter(location_type=location_type)
    
    # Category filter from sidebar
    category_id = request.GET.get('category')
    if category_id:
        jobs = jobs.filter(category_id=category_id)
    
    categories = JobCategory.objects.annotate(job_count=Count('jobs'))
    
    context = {
        'jobs': jobs[:50],
        'categories': categories,
        'search_form': form,
    }
    
    return render(request, 'jobs/job_list.html', context)


def job_detail(request, pk):
    """
    WHAT: View job details
    """
    
    job = get_object_or_404(
        Job.objects.select_related('company', 'category'),
        pk=pk
    )
    
    job.increment_view()
    
    has_applied = False
    is_saved = False
    user_company = None
    
    if request.user.is_authenticated:
        has_applied = JobApplication.objects.filter(
            job=job, applicant=request.user
        ).exists()
        
        is_saved = SavedJob.objects.filter(
            user=request.user, job=job
        ).exists()
        
        # Check if user is company admin
        user_company = Company.objects.filter(
            Q(owner=request.user) | Q(admins=request.user)
        ).first()
    
    # Similar jobs
    similar_jobs = Job.objects.filter(
        category=job.category,
        status='active'
    ).exclude(pk=pk)[:5]
    
    context = {
        'job': job,
        'has_applied': has_applied,
        'is_saved': is_saved,
        'user_company': user_company,
        'similar_jobs': similar_jobs,
    }
    
    return render(request, 'jobs/job_detail.html', context)


@login_required
def post_job(request, company_id=None):
    """
    WHAT: Post a new job (recruiters only)
    """
    
    # Check if user has a company
    company = None
    if company_id:
        company = get_object_or_404(Company, pk=company_id)
        if company.owner != request.user and request.user not in company.admins.all():
            messages.error(request, _('You are not authorized to post jobs for this company.'))
            return redirect('jobs:job_list')
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company
            job.save()
            form.save_m2m()
            messages.success(request, _('Job posted successfully!'))
            return redirect('jobs:job_detail', pk=job.pk)
    else:
        form = JobForm()
    
    context = {
        'form': form,
        'company': company,
    }
    
    return render(request, 'jobs/post_job.html', context)


@login_required
def apply_job(request, pk):
    """
    WHAT: Apply to a job
    """
    
    job = get_object_or_404(Job, pk=pk)
    
    # Check if already applied
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, _('You have already applied to this job.'))
        return redirect('jobs:job_detail', pk=pk)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = request.user
            application.applicant_name = request.user.get_full_name()
            application.applicant_email = request.user.email
            application.save()
            
            # Send real-time notification to recruiter
            from django.urls import reverse
            from user_notifications.utils import notify_user
            
            manage_url = reverse('jobs:manage_applications', kwargs={'job_id': job.pk})
            recipients = [job.company.owner]
            for admin in job.company.admins.all():
                if admin not in recipients:
                    recipients.append(admin)
                    
            for recipient in recipients:
                if recipient != request.user:
                    notify_user(
                        recipient=recipient,
                        notification_type='job_application',
                        title='New Job Application',
                        message=f'{request.user.get_full_name() or request.user.username} applied to your job listing: {job.title}',
                        actor=request.user,
                        url=manage_url
                    )
            
            messages.success(request, _('Application submitted successfully!'))
            return redirect('jobs:application_success', pk=application.pk)
    else:
        form = JobApplicationForm()
    
    context = {
        'job': job,
        'form': form,
    }
    
    return render(request, 'jobs/apply.html', context)


@login_required
def application_success(request, pk):
    """Application confirmation page"""
    application = get_object_or_404(JobApplication, pk=pk, applicant=request.user)
    return render(request, 'jobs/application_success.html', {'application': application})


@login_required
def my_applications(request):
    """
    WHAT: View user's job applications
    """
    
    applications = JobApplication.objects.filter(
        applicant=request.user
    ).select_related('job', 'job__company').order_by('-created_at')
    
    context = {
        'applications': applications,
    }
    
    return render(request, 'jobs/my_applications.html', context)


@login_required
def manage_applications(request, job_id):
    """
    WHAT: Manage applications for a job (recruiters only)
    """
    
    job = get_object_or_404(Job, pk=job_id)
    
    # Check permission
    company = job.company
    if company.owner != request.user and request.user not in company.admins.all():
        messages.error(request, _('You are not authorized to manage this job.'))
        return redirect('jobs:job_list')
    
    applications = job.applications.select_related('applicant').order_by('-created_at')
    
    context = {
        'job': job,
        'applications': applications,
    }
    
    return render(request, 'jobs/manage_applications.html', context)


@login_required
@require_POST
def update_application_status(request, app_id):
    """Update application status"""
    
    application = get_object_or_404(JobApplication, pk=app_id)
    
    # Check permission
    if application.job.company.owner != request.user and request.user not in application.job.company.admins.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    new_status = request.POST.get('status')
    if new_status in dict(JobApplication.STATUS_CHOICES):
        application.status = new_status
        application.save()
        
        # Send real-time notification to applicant
        from django.urls import reverse
        from user_notifications.utils import notify_user
        
        my_apps_url = reverse('jobs:my_applications')
        notify_user(
            recipient=application.applicant,
            notification_type='job_status',
            title='Job Application Update',
            message=f'Your application status for "{application.job.title}" has been updated to: {application.get_status_display()}',
            actor=request.user,
            url=my_apps_url
        )
        
        messages.success(request, _(f'Application status updated to {application.get_status_display()}'))
    
    return redirect('jobs:manage_applications', job_id=application.job.pk)


@login_required
@require_POST
def save_job(request, pk):
    """Save/Unsave a job"""
    
    job = get_object_or_404(Job, pk=pk)
    
    saved, created = SavedJob.objects.get_or_create(
        user=request.user,
        job=job
    )
    
    if not created:
        saved.delete()
        messages.info(request, _('Job removed from saved'))
    else:
        messages.success(request, _('Job saved!'))
    
    return redirect(request.META.get('HTTP_REFERER', 'jobs:job_list'))


@login_required
def saved_jobs(request):
    """View saved jobs"""
    
    saved = SavedJob.objects.filter(
        user=request.user
    ).select_related('job', 'job__company')
    
    context = {
        'saved_jobs': saved,
    }
    
    return render(request, 'jobs/saved_jobs.html', context)


@login_required
def create_company(request):
    """Create a company profile"""
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save(commit=False)
            company.owner = request.user
            company.save()
            messages.success(request, _('Company profile created!'))
            return redirect('jobs:post_job_company', company_id=company.pk)
    else:
        form = CompanyForm()
    
    return render(request, 'jobs/create_company.html', {'form': form})


@login_required
def recommended_jobs(request):
    """
    WHAT: Show personalized job recommendations
    WHY: Match jobs to user profile skills/bio using keyword overlap
    """
    user = request.user

    # Collect user's skill keywords from bio + skills fields
    user_text = ''
    if hasattr(user, 'bio') and user.bio:
        user_text += ' ' + user.bio
    if hasattr(user, 'skills') and user.skills:
        user_text += ' ' + user.skills
    if hasattr(user, 'headline') and user.headline:
        user_text += ' ' + user.headline

    user_keywords = [
        word.lower().strip()
        for word in user_text.split()
        if len(word) > 3
    ]

    active_jobs = Job.objects.filter(
        status='active'
    ).select_related('company', 'category')[:200]

    # Score each job by keyword matches
    scored = []
    for job in active_jobs:
        job_text = f'{job.title} {job.description}'.lower()
        score = sum(1 for kw in user_keywords if kw in job_text)
        if score > 0 or not user_keywords:
            scored.append((score, job))

    scored.sort(key=lambda x: x[0], reverse=True)
    recommended = [job for _, job in scored[:20]]

    # Fallback: if no profile info, show recent jobs
    if not recommended:
        recommended = list(
            Job.objects.filter(status='active')
            .select_related('company', 'category')
            .order_by('-posted_at')[:20]
        )

    context = {
        'jobs': recommended,
        'categories': JobCategory.objects.annotate(job_count=Count('jobs')),
        'search_form': JobSearchForm(),
        'is_recommended': True,
    }
    return render(request, 'jobs/job_list.html', context)
