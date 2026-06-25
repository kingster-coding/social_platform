"""
WHAT: Forms for feed app
WHY: Post creation and comments
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Post, Comment


class PostForm(forms.ModelForm):
    """
    WHAT: Form for creating/editing posts
    """
    
    class Meta:
        model = Post
        fields = ['content', 'image', 'video', 'privacy']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': _('What\'s on your mind?'),
                'class': 'post-content-input'
            }),
            'privacy': forms.Select(attrs={'class': 'privacy-select'}),
        }
        labels = {
            'content': '',
        }


class CommentForm(forms.ModelForm):
    """
    WHAT: Form for adding comments
    """
    
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'placeholder': _('Write a comment...'),
                'class': 'comment-input'
            })
        }
        labels = {
            'content': '',
        }