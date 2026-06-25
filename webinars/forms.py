"""
WHAT: Forms for webinars app
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Webinar, WebinarRegistration, WebinarQuestion, WebinarRating


class WebinarForm(forms.ModelForm):
    """Form for creating webinars"""
    
    class Meta:
        model = Webinar
        fields = [
            'title', 'description', 'thumbnail', 'cover_image',
            'category', 'tags', 'scheduled_at', 'duration_minutes',
            'access_type', 'max_attendees', 'registration_deadline',
            'price', 'enable_chat', 'enable_qa', 'enable_recording',
            'require_registration', 'send_reminders'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'tags': forms.TextInput(attrs={'placeholder': _('e.g., tech, business, education')}),
        }


class WebinarRegistrationForm(forms.ModelForm):
    """Form for webinar registration"""
    
    class Meta:
        model = WebinarRegistration
        fields = ['email', 'phone']
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': _('Optional')}),
        }


class QuestionForm(forms.ModelForm):
    """Form for asking questions"""
    
    class Meta:
        model = WebinarQuestion
        fields = ['question']
        widgets = {
            'question': forms.TextInput(attrs={
                'placeholder': _('Ask a question...'),
                'class': 'question-input'
            })
        }
        labels = {'question': ''}


class RatingForm(forms.ModelForm):
    """Form for rating webinars"""
    
    class Meta:
        model = WebinarRating
        fields = ['rating', 'review']
        widgets = {
            'review': forms.Textarea(attrs={'rows': 3, 'placeholder': _('Share your experience...')}),
        }


class WebinarSearchForm(forms.Form):
    """Search form for webinars"""
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Search webinars...')})
    )
    category = forms.ChoiceField(required=False, choices=[('', _('All Categories'))])
    access_type = forms.ChoiceField(
        required=False,
        choices=[('', _('All Types'))] + Webinar.ACCESS_CHOICES
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import WebinarCategory
        categories = WebinarCategory.objects.all()
        self.fields['category'].choices += [(c.id, c.name) for c in categories]