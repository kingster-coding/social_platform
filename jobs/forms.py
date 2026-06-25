"""
WHAT: Forms for jobs app
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Company, Job, JobApplication, JobAlert


class CompanyForm(forms.ModelForm):
    """Form for creating/editing company profile"""
    
    class Meta:
        model = Company
        fields = [
            'name', 'logo', 'cover', 'description', 'website',
            'industry', 'size', 'founded', 'headquarters'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class JobForm(forms.ModelForm):
    """Form for posting jobs"""
    
    class Meta:
        model = Job
        fields = [
            'title', 'category', 'description', 'requirements',
            'responsibilities', 'benefits', 'job_type', 'experience_level',
            'location_type', 'location', 'required_skills',
            'salary_min', 'salary_max', 'salary_currency', 'salary_period', 'show_salary',
            'application_deadline', 'vacancies'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'requirements': forms.Textarea(attrs={'rows': 5}),
            'responsibilities': forms.Textarea(attrs={'rows': 5}),
            'benefits': forms.Textarea(attrs={'rows': 3}),
            'application_deadline': forms.DateInput(attrs={'type': 'date'}),
            'required_skills': forms.SelectMultiple(attrs={'class': 'select2'}),
        }


class JobSearchForm(forms.Form):
    """Search form for jobs"""
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Job title, keywords, or company')})
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('City, state, or remote')})
    )
    job_type = forms.ChoiceField(
        choices=[('', _('All Job Types'))] + Job.JOB_TYPE_CHOICES,
        required=False
    )
    experience_level = forms.ChoiceField(
        choices=[('', _('All Experience Levels'))] + Job.EXPERIENCE_CHOICES,
        required=False
    )
    location_type = forms.ChoiceField(
        choices=[('', _('All Location Types'))] + Job.LOCATION_TYPE_CHOICES,
        required=False
    )


class JobApplicationForm(forms.ModelForm):
    """Form for applying to jobs"""
    
    class Meta:
        model = JobApplication
        fields = ['resume', 'cover_letter', 'additional_docs']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': _('Tell us why you are a great fit for this role...')
            })
        }


class JobAlertForm(forms.ModelForm):
    """Form for creating job alerts"""
    
    class Meta:
        model = JobAlert
        fields = ['title', 'keywords', 'location', 'job_type', 'category', 'frequency']