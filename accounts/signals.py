"""
WHAT: Django signals for automatic actions
WHY: Jab naya user create ho, uska Profile automatically create ho
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail

@receiver(post_save, sender='accounts.User')
def create_user_profile(sender, instance, created, **kwargs):
    """
    WHAT: Create Profile when User is created
    WHY: Har user ka profile hona mandatory hai

    NOTE: OTP email yahan NAHI bhejte — signal ke andar save() call hone se
    recursive post_save trigger ho sakta tha. OTP CustomSignupForm.save() ya
    adapter mein handle karo.
    """
    if created:
        from .models import Profile
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender='accounts.User')
def save_user_profile(sender, instance, **kwargs):
    """
    WHAT: Save Profile when User is saved
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()