"""
WHAT: Forms for groups app
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Group, GroupPost, GroupJoinRequest, GroupInvitation, GroupEvent


class GroupForm(forms.ModelForm):
    """Form for creating/editing groups"""
    
    class Meta:
        model = Group
        fields = [
            'name', 'description', 'cover_image', 'icon',
            'category', 'tags', 'visibility', 'requires_approval',
            'post_approval', 'allow_member_posts', 'allow_member_invites',
            'show_member_list', 'rules'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'rules': forms.Textarea(attrs={'rows': 4, 'placeholder': _('Group rules and guidelines...')}),
            'tags': forms.TextInput(attrs={'placeholder': _('e.g., tech, gaming, books')}),
        }


class GroupPostForm(forms.ModelForm):
    """Form for creating group posts"""
    
    class Meta:
        model = GroupPost
        fields = ['content', 'image', 'is_announcement']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': _('What\'s on your mind?')
            }),
        }


class JoinRequestForm(forms.ModelForm):
    """Form for joining a group"""
    
    class Meta:
        model = GroupJoinRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': _('Why do you want to join this group? (Optional)')
            }),
        }


class InvitationForm(forms.ModelForm):
    """Form for inviting members"""
    
    class Meta:
        model = GroupInvitation
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': _('Add a personal message (Optional)')
            }),
        }


class GroupEventForm(forms.ModelForm):
    """Form for creating group events"""
    
    class Meta:
        model = GroupEvent
        fields = [
            'title', 'description', 'location', 'is_online',
            'meeting_link', 'start_at', 'end_at', 'max_attendees'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class GroupSearchForm(forms.Form):
    """Search form for groups"""
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Search groups...')})
    )
    category = forms.ChoiceField(required=False, choices=[('', _('All Categories'))])
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import GroupCategory
        categories = GroupCategory.objects.all()
        self.fields['category'].choices += [(c.id, c.name) for c in categories]