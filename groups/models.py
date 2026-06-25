"""
WHAT: Groups app models
WHY: Facebook-style groups functionality
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.utils.text import slugify

User = settings.AUTH_USER_MODEL


class GroupCategory(models.Model):
    """
    WHAT: Categories for groups
    """
    
    name = models.CharField(_('category name'), max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('group category')
        verbose_name_plural = _('group categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Group(models.Model):
    """
    WHAT: Main group model
    """
    
    VISIBILITY_CHOICES = [
        ('public', _('Public')),
        ('private', _('Private')),
        ('secret', _('Secret')),
    ]
    
    # Basic Info
    name = models.CharField(_('group name'), max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(_('description'), max_length=2000)
    
    # Media
    cover_image = models.ImageField(_('cover photo'), upload_to='groups/covers/%Y/%m/', blank=True)
    icon = models.ImageField(_('group icon'), upload_to='groups/icons/%Y/%m/', blank=True)
    
    # Categorization
    category = models.ForeignKey(GroupCategory, on_delete=models.SET_NULL, null=True, related_name='groups')
    tags = models.CharField(_('tags'), max_length=500, blank=True)
    
    # Privacy Settings
    visibility = models.CharField(_('visibility'), max_length=10, choices=VISIBILITY_CHOICES, default='public')
    requires_approval = models.BooleanField(_('require admin approval to join'), default=True)
    post_approval = models.BooleanField(_('require admin approval for posts'), default=False)
    
    # Creator/Owner
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    
    # Settings
    allow_member_posts = models.BooleanField(_('allow members to post'), default=True)
    allow_member_invites = models.BooleanField(_('allow members to invite'), default=True)
    show_member_list = models.BooleanField(_('show member list to non-members'), default=True)
    
    # Rules
    rules = models.TextField(_('group rules'), blank=True, help_text=_('Rules for group members'))
    
    # Status
    is_active = models.BooleanField(_('active'), default=True)
    is_featured = models.BooleanField(_('featured'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analytics
    member_count = models.PositiveIntegerField(default=0)
    post_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')
        ordering = ['-member_count', '-created_at']
        indexes = [
            models.Index(fields=['-member_count']),
            models.Index(fields=['visibility', '-created_at']),
            models.Index(fields=['category', '-created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        # Auto-generate slug if blank
        if not self.slug and self.name:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Group.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        if is_new:
            # Auto-add creator as admin member
            GroupMember.objects.create(
                group=self,
                user=self.creator,
                role='admin',
                joined_at=timezone.now()
            )
    
    @property
    def is_public(self):
        return self.visibility == 'public'
    
    @property
    def is_private(self):
        return self.visibility == 'private'
    
    @property
    def is_secret(self):
        return self.visibility == 'secret'
    
    def get_member_count(self):
        return self.members.filter(is_banned=False).count()
    
    def update_member_count(self):
        self.member_count = self.get_member_count()
        self.save(update_fields=['member_count'])
    
    def is_member(self, user):
        if not user.is_authenticated:
            return False
        return self.members.filter(user=user, is_banned=False).exists()
    
    def is_admin(self, user):
        return self.members.filter(user=user, role='admin', is_banned=False).exists()
    
    def is_moderator(self, user):
        return self.members.filter(user=user, role__in=['admin', 'moderator'], is_banned=False).exists()
    
    def can_post(self, user):
        if not self.is_member(user):
            return False
        if self.post_approval and not self.is_moderator(user):
            return False
        return True
    
    def can_invite(self, user):
        if not self.is_member(user):
            return False
        if not self.allow_member_invites and not self.is_moderator(user):
            return False
        return True


class GroupMember(models.Model):
    """
    WHAT: Group membership
    """
    
    ROLE_CHOICES = [
        ('admin', _('Admin')),
        ('moderator', _('Moderator')),
        ('member', _('Member')),
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    
    role = models.CharField(_('role'), max_length=10, choices=ROLE_CHOICES, default='member')
    
    # Status
    is_banned = models.BooleanField(_('banned'), default=False)
    ban_reason = models.TextField(blank=True)
    
    # Invite tracking
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='group_invites_sent')
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('group member')
        verbose_name_plural = _('group members')
        unique_together = ['group', 'user']
        ordering = ['-role', 'joined_at']
        indexes = [
            models.Index(fields=['group', 'user']),
            models.Index(fields=['group', 'role']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.group.name} ({self.role})"
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.is_banned:
            self.group.update_member_count()
    
    def delete(self, *args, **kwargs):
        group = self.group
        super().delete(*args, **kwargs)
        group.update_member_count()


class GroupJoinRequest(models.Model):
    """
    WHAT: Join requests for private groups
    """
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='join_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_join_requests')
    
    message = models.TextField(_('message'), max_length=500, blank=True, help_text=_('Why do you want to join?'))
    
    status = models.CharField(_('status'), max_length=10, choices=STATUS_CHOICES, default='pending')
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_requests')
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('join request')
        verbose_name_plural = _('join requests')
        unique_together = ['group', 'user', 'status']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} -> {self.group.name}"
    
    def approve(self, processed_by):
        self.status = 'approved'
        self.processed_by = processed_by
        self.processed_at = timezone.now()
        self.save()
        
        # Create membership
        GroupMember.objects.get_or_create(
            group=self.group,
            user=self.user,
            defaults={'role': 'member'}
        )
    
    def reject(self, processed_by):
        self.status = 'rejected'
        self.processed_by = processed_by
        self.processed_at = timezone.now()
        self.save()


class GroupInvitation(models.Model):
    """
    WHAT: Invitations to join groups
    """
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('accepted', _('Accepted')),
        ('declined', _('Declined')),
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='invitations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invitations')
    
    message = models.TextField(max_length=500, blank=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('invitation')
        verbose_name_plural = _('invitations')
        unique_together = ['group', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.invited_by.username} invited {self.user.username} to {self.group.name}"
    
    def accept(self):
        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.save()
        
        GroupMember.objects.get_or_create(
            group=self.group,
            user=self.user,
            defaults={'role': 'member', 'invited_by': self.invited_by}
        )
    
    def decline(self):
        self.status = 'declined'
        self.responded_at = timezone.now()
        self.save()


class GroupPost(models.Model):
    """
    WHAT: Posts within groups
    """
    
    STATUS_CHOICES = [
        ('pending', _('Pending Approval')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_posts')
    
    content = models.TextField(_('content'), max_length=2000)
    image = models.ImageField(_('image'), upload_to='groups/posts/%Y/%m/', blank=True)
    
    # Approval
    status = models.CharField(_('status'), max_length=10, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_posts')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Pin
    is_pinned = models.BooleanField(_('pinned'), default=False)
    is_announcement = models.BooleanField(_('announcement'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analytics
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('group post')
        verbose_name_plural = _('group posts')
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['group', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.author.username} - {self.group.name}"
    
    def approve(self, approved_by):
        self.status = 'approved'
        self.approved_by = approved_by
        self.approved_at = timezone.now()
        self.save()
        self.group.post_count = self.group.posts.filter(status='approved').count()
        self.group.save(update_fields=['post_count'])


class GroupPostLike(models.Model):
    """
    WHAT: Likes on group posts
    """
    
    post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['post', 'user']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.post.like_count = self.post.likes.count()
        self.post.save(update_fields=['like_count'])


class GroupPostComment(models.Model):
    """
    WHAT: Comments on group posts
    """
    
    post = models.ForeignKey(GroupPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.post.comment_count = self.post.comments.count()
        self.post.save(update_fields=['comment_count'])


class GroupEvent(models.Model):
    """
    WHAT: Events within groups
    """
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='events')
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=2000)
    
    location = models.CharField(max_length=300, blank=True)
    is_online = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True)
    
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    
    max_attendees = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('group event')
        verbose_name_plural = _('group events')
        ordering = ['start_at']
    
    def __str__(self):
        return f"{self.title} - {self.group.name}"