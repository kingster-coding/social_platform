"""
WHAT: Webinars app models
WHY: Live video webinar platform with Jitsi integration
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL


class WebinarCategory(models.Model):
    """
    WHAT: Categories for webinars
    """
    
    name = models.CharField(_('category name'), max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = _('webinar category')
        verbose_name_plural = _('webinar categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Webinar(models.Model):
    """
    WHAT: Main webinar model
    """
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('scheduled', _('Scheduled')),
        ('live', _('Live Now')),
        ('ended', _('Ended')),
        ('cancelled', _('Cancelled')),
    ]
    
    ACCESS_CHOICES = [
        ('free', _('Free')),
        ('paid', _('Paid')),
        ('private', _('Private/Invite Only')),
    ]
    
    # Basic Info
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_webinars')
    title = models.CharField(_('title'), max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField(_('description'), max_length=5000)
    
    # Media
    thumbnail = models.ImageField(_('thumbnail'), upload_to='webinars/thumbnails/%Y/%m/', blank=True)
    cover_image = models.ImageField(_('cover image'), upload_to='webinars/covers/%Y/%m/', blank=True)
    
    # Categorization
    category = models.ForeignKey(WebinarCategory, on_delete=models.SET_NULL, null=True, related_name='webinars')
    tags = models.CharField(_('tags'), max_length=500, blank=True, help_text=_('Comma separated tags'))
    
    # Schedule
    scheduled_at = models.DateTimeField(_('scheduled date and time'))
    duration_minutes = models.PositiveIntegerField(_('duration (minutes)'), default=60)
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    
    # Access
    access_type = models.CharField(_('access type'), max_length=10, choices=ACCESS_CHOICES, default='free')
    max_attendees = models.PositiveIntegerField(_('max attendees'), default=100)
    registration_deadline = models.DateTimeField(_('registration deadline'), null=True, blank=True)
    
    # Pricing (if paid)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='INR')
    
    # Jitsi Integration
    room_name = models.CharField(max_length=100, unique=True, blank=True)
    jitsi_server = models.URLField(default='https://meet.jit.si')
    
    # Features
    enable_chat = models.BooleanField(_('enable live chat'), default=True)
    enable_qa = models.BooleanField(_('enable Q&A'), default=True)
    enable_recording = models.BooleanField(_('enable recording'), default=True)
    auto_record = models.BooleanField(_('auto record'), default=False)
    require_registration = models.BooleanField(_('require registration'), default=True)
    send_reminders = models.BooleanField(_('send email reminders'), default=True)
    
    # Status
    status = models.CharField(_('status'), max_length=15, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(_('featured'), default=False)
    
    # Recording
    recording_url = models.URLField(_('recording URL'), blank=True)
    recording_duration = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    registration_count = models.PositiveIntegerField(default=0)
    attendance_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('webinar')
        verbose_name_plural = _('webinars')
        ordering = ['scheduled_at']
        indexes = [
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['status', 'scheduled_at']),
            models.Index(fields=['host', 'scheduled_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.room_name:
            self.room_name = f"{self.slug}-{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)
    
    @property
    def is_upcoming(self):
        return self.status == 'scheduled' and self.scheduled_at > timezone.now()
    
    @property
    def is_live(self):
        return self.status == 'live'
    
    @property
    def is_ended(self):
        return self.status == 'ended'
    
    @property
    def ends_at(self):
        if self.started_at:
            return self.started_at + timezone.timedelta(minutes=self.duration_minutes)
        return self.scheduled_at + timezone.timedelta(minutes=self.duration_minutes)
    
    @property
    def time_until_start(self):
        if self.scheduled_at > timezone.now():
            delta = self.scheduled_at - timezone.now()
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            return f"{days}d {hours}h {minutes}m"
        return _("Starting soon")
    
    @property
    def registration_open(self):
        if not self.require_registration:
            return True
        if self.registration_deadline:
            return timezone.now() < self.registration_deadline
        return timezone.now() < self.scheduled_at
    
    @property
    def spots_left(self):
        return max(0, self.max_attendees - self.registration_count)
    
    @property
    def is_full(self):
        return self.registration_count >= self.max_attendees
    
    def get_jitsi_url(self):
        """Generate Jitsi meet URL"""
        return f"{self.jitsi_server}/{self.room_name}"
    
    def increment_view(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])


class WebinarRegistration(models.Model):
    """
    WHAT: Registration for webinars
    """
    
    STATUS_CHOICES = [
        ('registered', _('Registered')),
        ('attended', _('Attended')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
    ]
    
    webinar = models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webinar_registrations')
    
    # Registration Info
    registration_number = models.CharField(max_length=50, unique=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    
    # Status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='registered')
    attended_at = models.DateTimeField(null=True, blank=True)
    
    # Payment (if paid)
    payment_status = models.CharField(max_length=20, default='pending')
    payment_id = models.CharField(max_length=100, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Certificate
    certificate_issued = models.BooleanField(default=False)
    certificate_url = models.URLField(blank=True)
    
    # Timestamps
    registered_at = models.DateTimeField(auto_now_add=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('webinar registration')
        verbose_name_plural = _('webinar registrations')
        unique_together = ['webinar', 'user']
        ordering = ['-registered_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.webinar.title}"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.registration_number:
            self.registration_number = f"WEB-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
        if is_new:
            self.webinar.registration_count = self.webinar.registrations.count()
            self.webinar.save(update_fields=['registration_count'])
    
    def mark_attended(self):
        self.status = 'attended'
        self.attended_at = timezone.now()
        self.save()
        self.webinar.attendance_count = self.webinar.registrations.filter(status='attended').count()
        self.webinar.save(update_fields=['attendance_count'])


class WebinarSession(models.Model):
    """
    WHAT: Live session tracking
    """
    
    webinar = models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name='sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webinar_sessions')
    
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('webinar session')
        verbose_name_plural = _('webinar sessions')
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.webinar.title}"


class WebinarQuestion(models.Model):
    """
    WHAT: Q&A questions during webinar
    """
    
    webinar = models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name='questions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webinar_questions')
    
    question = models.TextField(max_length=500)
    is_answered = models.BooleanField(default=False)
    answer = models.TextField(blank=True)
    answered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='answered_questions')
    
    upvotes = models.PositiveIntegerField(default=0)
    is_pinned = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('question')
        verbose_name_plural = _('questions')
        ordering = ['-upvotes', '-created_at']
    
    def __str__(self):
        return self.question[:50]


class WebinarRating(models.Model):
    """
    WHAT: Rating and review for webinars
    """
    
    webinar = models.ForeignKey(Webinar, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webinar_ratings')
    
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    review = models.TextField(max_length=1000, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('rating')
        verbose_name_plural = _('ratings')
        unique_together = ['webinar', 'user']
    
    def __str__(self):
        return f"{self.user.email} - {self.rating}★"


class WebinarCertificate(models.Model):
    """
    WHAT: Attendance certificates
    """
    
    registration = models.OneToOneField(WebinarRegistration, on_delete=models.CASCADE, related_name='certificate')
    certificate_number = models.CharField(max_length=50, unique=True)
    pdf_file = models.FileField(upload_to='webinars/certificates/%Y/%m/', blank=True)
    qr_code = models.ImageField(upload_to='webinars/qrcodes/%Y/%m/', blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    verification_url = models.URLField(blank=True)
    
    class Meta:
        verbose_name = _('certificate')
        verbose_name_plural = _('certificates')
    
    def __str__(self):
        return f"Certificate: {self.registration.user.email} - {self.registration.webinar.title}"