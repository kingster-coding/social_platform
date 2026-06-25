from django import forms
from django.utils.translation import gettext_lazy as _
from allauth.account.forms import SignupForm
from .models import User, Profile
from typing import cast

class CustomSignupForm(SignupForm):
    """
    WHAT: Custom Signup Form for django-allauth
    WHY: Required by settings.py to ensure compatibility with our custom User model
    """
    def save(self, request):
        user = cast(User, super().save(request))
        # OTP email yahan bhejo — sirf actual web signup par, createsuperuser par nahi
        try:
            user.send_otp_email()
        except Exception:
            pass  # Email fail hone pe signup block nahi hoga
        return user

class OTPVerificationForm(forms.Form):
    """
    WHAT: Form to take 6-digit OTP from user
    """
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={'placeholder': '123456', 'class': 'form-control text-center', 'autocomplete': 'one-time-code'})
    )

class UserProfileForm(forms.ModelForm):
    """
    WHAT: Unified form for editing custom User fields and linked Profile fields
    """
    pronouns = forms.CharField(max_length=20, required=False, label=_("Pronouns"), help_text=_("e.g., he/him, she/her, they/them"))
    gender = forms.ChoiceField(choices=Profile.GENDER_CHOICES, required=False, label=_("Gender"))
    phone = forms.CharField(max_length=15, required=False, label=_("Phone Number"))
    linkedin = forms.URLField(required=False, label=_("LinkedIn Profile URL"))
    twitter = forms.URLField(required=False, label=_("Twitter/X Profile URL"))
    github = forms.URLField(required=False, label=_("GitHub Profile URL"))
    instagram = forms.URLField(required=False, label=_("Instagram Profile URL"))

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'bio', 'location', 'website', 'birth_date', 'avatar', 'cover_photo']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            profile, _ = Profile.objects.get_or_create(user=instance)
            initial = kwargs.get('initial', {})
            initial['pronouns'] = profile.pronouns
            initial['gender'] = profile.gender
            initial['phone'] = profile.phone
            initial['linkedin'] = profile.linkedin
            initial['twitter'] = profile.twitter
            initial['github'] = profile.github
            initial['instagram'] = profile.instagram
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.pronouns = self.cleaned_data.get('pronouns', '')
            profile.gender = self.cleaned_data.get('gender', '')
            profile.phone = self.cleaned_data.get('phone', '')
            profile.linkedin = self.cleaned_data.get('linkedin', '')
            profile.twitter = self.cleaned_data.get('twitter', '')
            profile.github = self.cleaned_data.get('github', '')
            profile.instagram = self.cleaned_data.get('instagram', '')
            profile.save()
        return user

class UserSettingsForm(forms.ModelForm):
    """
    WHAT: Form for managing privacy settings
    """
    class Meta:
        model = User
        fields = ['is_private']
        widgets = {
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
