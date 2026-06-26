"""
WHAT: Forms for accounts app
WHY: Custom registration form (Name, Email, Phone, Password) + OTP verification
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from allauth.account.forms import SignupForm
from .models import User, Profile
from typing import cast
import re


# ============================================
# STEP 1 — REGISTRATION FORM
# ============================================
class RegisterStep1Form(forms.Form):
    """
    WHAT: Custom registration form — replaces allauth default signup
    WHY: We need full_name + phone_number fields.
         Username is auto-generated, user does NOT set it.
    """
    phone_validator = RegexValidator(
        regex=r'^\+?[0-9]{10,15}$',
        message=_('Enter a valid phone number (10-15 digits, optionally starting with +)')
    )

    first_name = forms.CharField(
        max_length=50,
        label=_('First Name'),
        widget=forms.TextInput(attrs={
            'placeholder': 'Mayank',
            'id': 'id_first_name',
            'autocomplete': 'given-name',
        })
    )

    last_name = forms.CharField(
        max_length=50,
        label=_('Last Name'),
        widget=forms.TextInput(attrs={
            'placeholder': 'Sharma',
            'id': 'id_last_name',
            'autocomplete': 'family-name',
        })
    )

    email = forms.EmailField(
        label=_('Email Address'),
        widget=forms.EmailInput(attrs={
            'placeholder': 'you@example.com',
            'id': 'id_email',
            'autocomplete': 'email',
        })
    )

    phone_number = forms.CharField(
        max_length=15,
        label=_('Phone Number'),
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'placeholder': '9876543210',
            'id': 'id_phone_number',
            'inputmode': 'tel',
            'autocomplete': 'tel',
        })
    )

    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Min 8 characters',
            'id': 'id_password1',
            'autocomplete': 'new-password',
        })
    )

    password2 = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repeat password',
            'id': 'id_password2',
            'autocomplete': 'new-password',
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _('This email is already registered. Please log in instead.')
            )
        return email

    def clean_phone_number(self):
        phone = re.sub(r'\s+', '', self.cleaned_data.get('phone_number', ''))
        # Strip leading + for storage but keep digits only check
        digits = re.sub(r'\D', '', phone)
        if len(digits) < 10:
            raise forms.ValidationError(_('Phone number must have at least 10 digits.'))
        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError(
                _('This phone number is already registered.')
            )
        return phone

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get('password1')
        pw2 = cleaned_data.get('password2')
        if pw1 and pw2 and pw1 != pw2:
            self.add_error('password2', _('Passwords do not match.'))
        return cleaned_data


# ============================================
# OTP VERIFICATION FORM
# ============================================
class OTPVerificationForm(forms.Form):
    """
    WHAT: Form to take 6-digit OTP from user (used in verify_otp page)
    """
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': '123456',
            'class': 'form-control text-center',
            'autocomplete': 'one-time-code'
        })
    )


# ============================================
# ALLAUTH COMPAT — kept for admin/social logins
# ============================================
class CustomSignupForm(SignupForm):
    """
    WHAT: Fallback allauth signup form (for admin/social login compatibility)
    WHY: Required by settings.py ACCOUNT_FORMS
    """
    def save(self, request):
        user = cast(User, super().save(request))
        try:
            user.send_otp_email()
        except Exception:
            pass
        return user


# ============================================
# PROFILE EDIT FORM
# ============================================
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


# ============================================
# SETTINGS FORM
# ============================================
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