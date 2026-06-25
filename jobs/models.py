"""
WHAT: Jobs app models
WHY: LinkedIn-style job posting and application system
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Company(models.Model):
    """
    WHAT: Company profile for recruiters
    WHY: Job postings belong to companies
    """
    
    SIZE_CHOICES = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1000+', '1000+ employees'),
    ]
    
    name = models.CharField(_('company name'), max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    logo = models.ImageField(_('logo'), upload_to='companies/logos/', blank=True)
    cover = models.ImageField(_('cover image'), upload_to='companies/covers/', blank=True)
    
    description = models.TextField(_('description'), max_length=2000)
    website = models.URLField(_('website'), blank=True)
    industry = models.CharField(_('industry'), max_length=100)
    size = models.CharField(_('company size'), max_length=20, choices=SIZE_CHOICES)
    founded = models.IntegerField(_('founded year'), null=True, blank=True)
    headquarters = models.CharField(_('headquarters'), max_length=200, blank=True)
    
    # Verification
    is_verified = models.BooleanField(_('verified'), default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Owners/Admins
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_companies')
    admins = models.ManyToManyField(User, related_name='admin_companies', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('company')
        verbose_name_plural = _('companies')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_logo_url(self):
        if self.logo:
            return self.logo.url
        return f'https://ui-avatars.com/api/?name={self.name}&background=1877f2&color=fff&size=100'


class JobCategory(models.Model):
    """
    WHAT: Job categories/industries
    """
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = _('job category')
        verbose_name_plural = _('job categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Skill(models.Model):
    """
    WHAT: Skills for jobs and seekers
    """
    
    name = models.CharField(max_length=100, unique=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Job(models.Model):
    """
    WHAT: Job posting model
    """
    
    JOB_TYPE_CHOICES = [
        ('full_time', _('Full-time')),
        ('part_time', _('Part-time')),
        ('contract', _('Contract')),
        ('internship', _('Internship')),
        ('freelance', _('Freelance')),
    ]
    
    EXPERIENCE_CHOICES = [
        ('entry', _('Entry Level (0-2 years)')),
        ('mid', _('Mid Level (3-5 years)')),
        ('senior', _('Senior Level (6-10 years)')),
        ('lead', _('Lead/Manager (10+ years)')),
        ('executive', _('Executive')),
    ]
    
    LOCATION_TYPE_CHOICES = [
        ('onsite', _('On-site')),
        ('remote', _('Remote')),
        ('hybrid', _('Hybrid')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('paused', _('Paused')),
        ('closed', _('Closed')),
        ('filled', _('Filled')),
    ]
    
    SALARY_PERIOD_CHOICES = [
        ('hourly', _('Hourly')),
        ('monthly', _('Monthly')),
        ('yearly', _('Yearly')),
    ]
    
    # Basic Info
    title = models.CharField(_('job title'), max_length=200)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs')
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, related_name='jobs')
    
    # Description
    description = models.TextField(_('job description'), max_length=5000)
    requirements = models.TextField(_('requirements'), max_length=2000)
    responsibilities = models.TextField(_('responsibilities'), max_length=2000)
    benefits = models.TextField(_('benefits'), max_length=1000, blank=True)
    
    # Details
    job_type = models.CharField(_('job type'), max_length=20, choices=JOB_TYPE_CHOICES)
    experience_level = models.CharField(_('experience level'), max_length=20, choices=EXPERIENCE_CHOICES)
    location_type = models.CharField(_('location type'), max_length=20, choices=LOCATION_TYPE_CHOICES)
    location = models.CharField(_('location'), max_length=200, help_text=_('City, State, Country'))
    
    # Skills
    required_skills = models.ManyToManyField(Skill, related_name='jobs', blank=True)
    
    # Salary
    salary_min = models.IntegerField(_('minimum salary'), null=True, blank=True)
    salary_max = models.IntegerField(_('maximum salary'), null=True, blank=True)
    salary_currency = models.CharField(max_length=3, default='INR')
    salary_period = models.CharField(max_length=10, choices=SALARY_PERIOD_CHOICES, default='yearly')
    show_salary = models.BooleanField(_('show salary'), default=True)
    
    # Application
    application_deadline = models.DateField(_('application deadline'), null=True, blank=True)
    vacancies = models.PositiveIntegerField(_('number of vacancies'), default=1)
    application_url = models.URLField(_('external application URL'), blank=True)
    
    # Status
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='active')
    is_featured = models.BooleanField(_('featured'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    posted_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    application_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('job')
        verbose_name_plural = _('jobs')
        ordering = ['-is_featured', '-posted_at']
        indexes = [
            models.Index(fields=['-posted_at']),
            models.Index(fields=['company', '-posted_at']),
            models.Index(fields=['category', '-posted_at']),
            models.Index(fields=['location', 'job_type']),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company.name}"
    
    @property
    def is_active(self):
        if self.status != 'active':
            return False
        if self.application_deadline and self.application_deadline < timezone.now().date():
            return False
        return True
    
    @property
    def salary_display(self):
        if not self.show_salary or (not self.salary_min and not self.salary_max):
            return _('Not disclosed')
        
        def format_salary(amount):
            if amount >= 10000000:
                return f"₹{amount/10000000:.1f}Cr"
            elif amount >= 100000:
                return f"₹{amount/100000:.1f}L"
            return f"₹{amount:,}"
        
        if self.salary_min and self.salary_max:
            return f"{format_salary(self.salary_min)} - {format_salary(self.salary_max)}"
        elif self.salary_min:
            return f"From {format_salary(self.salary_min)}"
        else:
            return f"Up to {format_salary(self.salary_max)}"
    
    def increment_view(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])


class JobApplication(models.Model):
    """
    WHAT: Job application model
    """
    
    STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('reviewed', _('Reviewed')),
        ('shortlisted', _('Shortlisted')),
        ('interview', _('Interview Scheduled')),
        ('offered', _('Offer Made')),
        ('hired', _('Hired')),
        ('rejected', _('Rejected')),
        ('withdrawn', _('Withdrawn')),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_applications')
    
    # Application Materials
    resume = models.FileField(_('resume'), upload_to='applications/resumes/%Y/%m/')
    cover_letter = models.TextField(_('cover letter'), max_length=2000, blank=True)
    additional_docs = models.FileField(_('additional documents'), upload_to='applications/docs/%Y/%m/', blank=True)
    
    # Applicant Info (snapshot at time of application)
    applicant_name = models.CharField(max_length=200)
    applicant_email = models.EmailField()
    applicant_phone = models.CharField(max_length=20, blank=True)
    
    # Status
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(_('internal notes'), blank=True, help_text=_('Notes for recruiters only'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('job application')
        verbose_name_plural = _('job applications')
        unique_together = ['job', 'applicant']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.applicant_name} - {self.job.title}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.job.application_count = self.job.applications.count()
            self.job.save(update_fields=['application_count'])


class SavedJob(models.Model):
    """
    WHAT: Saved/Bookmarked jobs
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_jobs')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('saved job')
        verbose_name_plural = _('saved jobs')
        unique_together = ['user', 'job']
        ordering = ['-created_at']


class JobAlert(models.Model):
    """
    WHAT: Job alert subscriptions
    """
    
    FREQUENCY_CHOICES = [
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
        ('instant', _('Instant')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_alerts')
    title = models.CharField(_('alert name'), max_length=200)
    keywords = models.CharField(_('keywords'), max_length=500, blank=True)
    location = models.CharField(_('location'), max_length=200, blank=True)
    job_type = models.CharField(max_length=20, choices=Job.JOB_TYPE_CHOICES, blank=True)
    category = models.ForeignKey(JobCategory, on_delete=models.SET_NULL, null=True, blank=True)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='weekly')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('job alert')
        verbose_name_plural = _('job alerts')
        ordering = ['-created_at']