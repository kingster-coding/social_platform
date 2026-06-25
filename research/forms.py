"""
WHAT: Forms for research app
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import ResearchPaper, PaperComment, ResearchCategory


class PaperUploadForm(forms.ModelForm):
    """
    WHAT: Form for uploading research papers
    """
    
    class Meta:
        model = ResearchPaper
        fields = [
            'title', 'abstract', 'keywords', 'file', 'cover_image',
            'category', 'journal_name', 'publication_date', 'doi',
            'additional_authors', 'access_level', 'allow_comments', 'allow_download'
        ]
        widgets = {
            'abstract': forms.Textarea(attrs={'rows': 5}),
            'keywords': forms.TextInput(attrs={'placeholder': _('e.g., AI, Machine Learning, NLP')}),
            'publication_date': forms.DateInput(attrs={'type': 'date'}),
        }


class PaperSearchForm(forms.Form):
    """
    WHAT: Search form for papers
    """
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search by title, author, keywords...'),
            'class': 'search-input'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=ResearchCategory.objects.all(),
        required=False,
        empty_label=_('All Categories')
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', _('Newest')),
            ('-view_count', _('Most Viewed')),
            ('-download_count', _('Most Downloaded')),
            ('-citation_count', _('Most Cited')),
            ('title', _('Title (A-Z)')),
        ],
        required=False,
        initial='-created_at'
    )


class PaperCommentForm(forms.ModelForm):
    """
    WHAT: Form for paper comments/reviews
    """
    
    class Meta:
        model = PaperComment
        fields = ['content', 'is_review']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': _('Share your thoughts or peer review...')
            })
        }