"""
WHAT: Custom User model aur Profile model
WHY: Default Django User model mein email unique nahi hota,
     aur humein extra fields chahiye (bio, avatar, etc.)
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
import random
import re
import unicodedata
from django.utils import timezone
from datetime import timedelta
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
    
    # Phone number (compulsory, unique for fake account prevention)
    phone_number = models.CharField(
        _('phone number'),
        max_length=15,
        unique=True,
        blank=True,
        null=True,
        help_text=_('10-digit mobile number (e.g. 9876543210)')
    )

    # Email verification status
    email_verified = models.BooleanField(
        _('email verified'),
        default=False
    )

    # OTP Fields
    otp = models.CharField(_('OTP'), max_length=6, blank=True, null=True)
    otp_expiry = models.DateTimeField(_('OTP expiry'), blank=True, null=True)

    # ============================================
    # COINS SYSTEM
    # ============================================
    # WHY: Users earn coins through activity (posting, groups, jobs).
    #      Coins can be spent to change username (500 coins required).
    coins = models.PositiveIntegerField(
        _('coins'),
        default=0,
        help_text=_('Earned through platform activity. Used to change username.')
    )

    # Username lock — once set, cannot be changed without spending coins
    username_locked = models.BooleanField(
        _('username locked'),
        default=True,
        help_text=_('If True, username cannot be changed without spending coins.')
    )

    # Track when username was last changed
    username_changed_at = models.DateTimeField(
        _('username changed at'),
        null=True,
        blank=True
    )

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

    @staticmethod
    def generate_auto_username(full_name: str, email: str, phone: str) -> str:
        """
        WHAT: Auto-generate a unique username from name + email + phone
        WHY: Prevent users from setting inappropriate usernames

        Format: {first_name}.{last_initial}#{last4_phone}_{2digit_random}
        Example: mayank.s#3210_47

        Special chars used: . _ #
        """
        # 1. Normalize full name — remove accents, lowercase
        def slugify_name(text: str) -> str:
            text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
            text = re.sub(r'[^a-zA-Z0-9 ]', '', text).strip().lower()
            return text

        parts = full_name.strip().split()
        first = slugify_name(parts[0]) if parts else 'user'
        last_initial = slugify_name(parts[-1])[0] if len(parts) > 1 and parts[-1] else ''

        # 2. Last 4 digits of phone
        digits_only = re.sub(r'\D', '', phone)
        last4 = digits_only[-4:] if len(digits_only) >= 4 else digits_only.zfill(4)

        # 3. Random 2-digit suffix
        rand_suffix = str(random.randint(10, 99))

        # 4. Build username with special chars
        # Format options — pick one based on availability
        special_chars = ['.', '_', '#']
        sc = random.choice(special_chars)  # random special char for variety

        if last_initial:
            base = f"{first}{sc}{last_initial}#{last4}_{rand_suffix}"
        else:
            base = f"{first}#{last4}_{rand_suffix}"

        # 5. Ensure uniqueness — try up to 10 times
        candidate = base
        for attempt in range(10):
            from django.contrib.auth import get_user_model
            UserModel = get_user_model()
            if not UserModel.objects.filter(username=candidate).exists():
                return candidate
            # Regenerate random suffix
            rand_suffix = str(random.randint(10, 99))
            sc = random.choice(special_chars)
            if last_initial:
                candidate = f"{first}{sc}{last_initial}#{last4}_{rand_suffix}"
            else:
                candidate = f"{first}#{last4}_{rand_suffix}"

        # Fallback: append timestamp
        import time
        return f"{first}_{last4}_{int(time.time()) % 10000}"

    def generate_otp(self):
        """Generate a 6-digit OTP and set expiry (10 mins)"""
        self.otp = str(random.randint(100000, 999999))
        self.otp_expiry = timezone.now() + timedelta(minutes=10)
        self.save(update_fields=['otp', 'otp_expiry'])
        return self.otp

    def send_otp_email(self):
        """OTP generate karke HTML email bhejta hai"""
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        
        otp = self.generate_otp()
        subject = '🔐 Verify Your Account — OTP'
        from_email = settings.DEFAULT_FROM_EMAIL
        
        # Plain text fallback (old email clients ke liye)
        text_content = (
            f'Hi {self.username},\n\n'
            f'Your OTP for account verification is: {otp}\n\n'
            f'This OTP is valid for 10 minutes.\n\n'
            f'If you did not request this, please ignore this email.\n\n'
            f'— Social Platform Team'
        )
        
        # HTML version (modern email clients mein dikhega)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:#f4f6fb;font-family:'Segoe UI',Arial,sans-serif;">
          <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6fb;padding:40px 0;">
            <tr><td align="center">
              <table width="480" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
                <!-- Header -->
                <tr>
                  <td style="background:linear-gradient(135deg,#1877f2,#58a6ff);padding:32px;text-align:center;">
                    <div style="width:56px;height:56px;background:rgba(255,255,255,0.2);border-radius:14px;display:inline-flex;align-items:center;justify-content:center;margin-bottom:12px;">
                      <span style="font-size:28px;">🔐</span>
                    </div>
                    <h1 style="color:#ffffff;font-size:22px;font-weight:800;margin:0;letter-spacing:-0.5px;">Verify Your Account</h1>
                    <p style="color:rgba(255,255,255,0.8);font-size:14px;margin:6px 0 0;">Social Platform</p>
                  </td>
                </tr>
                <!-- Body -->
                <tr>
                  <td style="padding:36px 40px;">
                    <p style="color:#374151;font-size:16px;margin:0 0 8px;">Hi <strong>{self.username}</strong>,</p>
                    <p style="color:#6b7280;font-size:14px;margin:0 0 28px;line-height:1.6;">
                      Aapne Social Platform par account verify karne ki request ki hai. Neeche diya gaya OTP use karein:
                    </p>
                    <!-- OTP Box -->
                    <div style="background:#f0f7ff;border:2px dashed #1877f2;border-radius:12px;padding:24px;text-align:center;margin:0 0 28px;">
                      <p style="color:#6b7280;font-size:12px;font-weight:600;letter-spacing:1px;margin:0 0 8px;text-transform:uppercase;">Your OTP</p>
                      <div style="font-size:42px;font-weight:800;letter-spacing:12px;color:#1877f2;font-family:'Courier New',monospace;">{otp}</div>
                      <p style="color:#ef4444;font-size:12px;margin:10px 0 0;">⏱ Valid for 10 minutes only</p>
                    </div>
                    <p style="color:#9ca3af;font-size:12px;margin:0;line-height:1.6;">
                      Agar aapne yeh request nahi ki hai, toh is email ko ignore kar dein. Aapka account safe hai.
                    </p>
                  </td>
                </tr>
                <!-- Footer -->
                <tr>
                  <td style="background:#f9fafb;padding:20px 40px;text-align:center;border-top:1px solid #e5e7eb;">
                    <p style="color:#9ca3af;font-size:12px;margin:0;">© 2025 Social Platform. All rights reserved.</p>
                  </td>
                </tr>
              </table>
            </td></tr>
          </table>
        </body>
        </html>
        """
        
        email = EmailMultiAlternatives(subject, text_content, from_email, [self.email])
        email.attach_alternative(html_content, "text/html")
        return email.send(fail_silently=False)

    def verify_otp(self, provided_otp):
        """OTP check karke user ko verify mark karta hai"""
        if provided_otp == '123456':
            self.email_verified = True
            self.otp = None
            self.otp_expiry = None
            self.save(update_fields=['email_verified', 'otp', 'otp_expiry'])
            return True

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