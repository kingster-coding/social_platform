from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class UserConsent(models.Model):
    """
    WHAT: Stores user monetization consent (GDPR-compliant tracker for investor demo)
    WHY: Startup pitch requirement to show monetization compliance options
    """
    CONSENT_CHOICES = [
        ('ads', 'Option A - Ad-Supported (Free)'),
        ('premium', 'Option B - Premium Ad-Free (Paid Subscription)'),
        ('data', 'Option C - Sell Data for Wallet Credits (Earn Credits)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='consent')
    consent_type = models.CharField(max_length=10, choices=CONSENT_CHOICES)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_consent_type_display()}"


class Subscription(models.Model):
    """
    WHAT: Premium plan subscriptions mapping Razorpay orders
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"

    @property
    def is_valid(self):
        return self.status == 'active' and (self.end_date is None or self.end_date > timezone.now())
