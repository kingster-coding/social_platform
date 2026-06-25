"""
WHAT: Custom User model aur Profile model
WHY: Default Django User model mein email unique nahi hota,
     aur humein extra fields chahiye (bio, avatar, etc.)
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import random
from django.utils import timezone
from django.core.mail import send_mail

# ============================================
# CUSTOM USER MODEL
# ============================================
class User(AbstractUser):
    """
    WHAT: Custom User model - AbstractUser ko extend kiya hai
    WHY: Email ko unique banana hai aur future mein extra fields add karne hain
    
    AbstractUser kya hai?
    - Django ka built-in User model jisme username, password, email, first_name, last_name already hote hain
    - Hum isko extend karke apne fields add kar sakte hain
    """
    
    # Email ko unique banaya (default mein nahi hota)
    email = models.EmailField(
        _('email address'), 
        unique=True,  # ⭐ Har user ka email unique hoga
        help_text=_('Required. Enter a valid email address.')
    )
    
    # Extra fields jo humein chahiye
    bio = models.TextField(
        _('bio'), 
        max_length=500, 
        blank=True,
        help_text=_('Tell us about yourself (max 500 characters)')
    )
    
    location = models.CharField(
        _('location'), 
        max_length=100, 
        blank=True,
        help_text=_('City, Country')
    )
    
    website = models.URLField(
        _('website'), 
        max_length=200, 
        blank=True
    )
    
    birth_date = models.DateField(
        _('birth date'), 
        null=True, 
        blank=True
    )
    
    # Profile picture (Cloudinary pe store hoga baad mein)
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',  # media/avatars/ folder mein save hoga
        blank=True,
        null=True,
        help_text=_('Profile picture')
    )
    
    # Cover photo (FB-style)
    cover_photo = models.ImageField(
        _('cover photo'),
        upload_to='covers/',
        blank=True,
        null=True,
        help_text=_('Cover photo for profile')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Privacy settings
    is_private = models.BooleanField(
        _('private account'),
        default=False,
        help_text=_('If checked, only followers can see your posts')
    )
    
    following = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='followers',
        blank=True,
        verbose_name=_('following')
    )
    
    # Email verification status
    email_verified = models.BooleanField(
        _('email verified'),
        default=False
    )
    
    # OTP Fields
    otp = models.CharField(_('OTP'), max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(_('OTP expiry'), blank=True, null=True)
    
    # Required for AbstractUser
    USERNAME_FIELD = 'email'  # ⭐ Email se login hoga (username nahi)
    REQUIRED_FIELDS = ['username']  # Email ke alawa username bhi puchhega createsuperuser
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return full name or username if not available"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_short_name(self):
        """Return first name or username"""
        return self.first_name or self.username

    def generate_otp(self):
        """Generate a 6-digit OTP and set expiry (10 mins)"""
        self.otp = str(random.randint(100000, 999999))
        self.otp_expiry = timezone.now() + timezone.timedelta(minutes=10)
        self.save(update_fields=['otp', 'otp_expiry'])
        return self.otp

    def send_otp_email(self):
        """OTP generate karke email bhejta hai"""
        otp = self.generate_otp()
        subject = 'Verify your account - OTP'
        message = f'Hi {self.username}, your OTP for account verification is: {otp}. It is valid for 10 minutes.'
        from_email = 'noreply@socialplatform.com'
        
        return send_mail(
            subject,
            message,
            from_email,
            [self.email],
            fail_silently=False,
        )

    def verify_otp(self, provided_otp):
        """OTP check karke user ko verify mark karta hai"""
        if (self.otp == provided_otp and 
            self.otp_expiry and 
            self.otp_expiry > timezone.now()):
            self.email_verified = True
            self.otp = None
            self.otp_expiry = None
            self.save(update_fields=['email_verified', 'otp', 'otp_expiry'])
            return True
        return False


# ============================================
# USER PROFILE MODEL (Optional - for extra data)
# ============================================
class Profile(models.Model):
    """
    WHAT: Extra profile information
    WHY: Kuch data jo main User model mein nahi rakhna chahte
    
    OneToOneField kya hai?
    - Har User ka sirf EK Profile hoga
    - Har Profile sirf EK User se belong karega
    """
    
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
        ('N', _('Prefer not to say')),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,  # User delete hone pe Profile bhi delete
        related_name='profile'
    )
    
    # Additional fields
    pronouns = models.CharField(
        _('pronouns'),
        max_length=20,
        blank=True,
        help_text=_('e.g., he/him, she/her, they/them')
    )
    
    gender = models.CharField(
        _('gender'),
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True
    )
    
    phone = models.CharField(
        _('phone number'),
        max_length=15,
        blank=True
    )
    
    # Social links
    linkedin = models.URLField(_('LinkedIn'), blank=True)
    twitter = models.URLField(_('Twitter/X'), blank=True)
    github = models.URLField(_('GitHub'), blank=True)
    instagram = models.URLField(_('Instagram'), blank=True)
    
    # Privacy
    show_email = models.BooleanField(_('show email publicly'), default=False)
    show_birth_date = models.BooleanField(_('show birth date'), default=False)
    
    # Analytics
    profile_views = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.email}'s profile"
    
    def increment_views(self):
        """Profile view count badhao"""
        self.profile_views += 1
        self.save(update_fields=['profile_views'])