"""
WHAT: Forms for reels app
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Reel, ReelComment


class ReelForm(forms.ModelForm):
    """
    WHAT: Form for uploading reels
    """
    
    class Meta:
        model = Reel
        fields = ['title', 'caption', 'video', 'thumbnail', 'privacy', 'allow_comments']
        widgets = {
            'caption': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': _('Write a caption... #hashtags')
            }),
            'title': forms.TextInput(attrs={
                'placeholder': _('Title (optional)')
            }),
        }


class ReelCommentForm(forms.ModelForm):
    """
    WHAT: Form for reel comments
    """
    
    class Meta:
        model = ReelComment
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': _('Add a comment...'),
                'class': 'comment-input'
            })
        }
        labels = {'content': ''}