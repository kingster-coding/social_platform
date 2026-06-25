"""
WHAT: Feed app models - Post, Like, Comment, Share, Save
WHY: Facebook-style feed functionality ke liye
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

User = settings.AUTH_USER_MODEL


class Post(models.Model):
    """
    WHAT: Main Post model - text, image, video posts ke liye
    WHY: Users apne thoughts, photos, videos share kar sakein
    """
    
    PRIVACY_CHOICES = [
        ('public', _('Public')),
        ('friends', _('Friends Only')),
        ('private', _('Only Me')),
    ]
    
    # Post content
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='posts',
        verbose_name=_('author')
    )
    
    content = models.TextField(
        _('content'),
        max_length=2000,
        blank=True,
        help_text=_('What\'s on your mind?')
    )
    
    # Media
    image = models.ImageField(
        _('image'),
        upload_to='posts/images/%Y/%m/',
        blank=True,
        null=True
    )
    
    video = models.FileField(
        _('video'),
        upload_to='posts/videos/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Privacy and settings
    privacy = models.CharField(
        _('privacy'),
        max_length=10,
        choices=PRIVACY_CHOICES,
        default='public'
    )
    
    is_pinned = models.BooleanField(
        _('pinned'),
        default=False,
        help_text=_('Pin to top of feed')
    )
    
    allow_comments = models.BooleanField(
        _('allow comments'),
        default=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Scheduled posts
    scheduled_at = models.DateTimeField(
        _('schedule for'),
        null=True,
        blank=True,
        help_text=_('Leave empty to publish now')
    )
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.author.username}'s post - {self.created_at.strftime('%Y-%m-%d')}"
    
    @property
    def is_published(self):
        """Check if scheduled post should be visible"""
        if self.scheduled_at:
            return self.scheduled_at <= timezone.now()
        return True
    
    @property
    def total_likes(self):
        return self.likes.count()
    
    @property
    def total_comments(self):
        return self.comments.count()
    
    @property
    def total_shares(self):
        return self.shares.count()
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('feed:post_detail', kwargs={'pk': self.pk})


class Like(models.Model):
    """
    WHAT: Post likes with reaction types
    WHY: Facebook-style reactions (Like, Love, Haha, etc.)
    """
    
    REACTION_CHOICES = [
        ('like', '👍 Like'),
        ('love', '❤️ Love'),
        ('haha', '😆 Haha'),
        ('wow', '😮 Wow'),
        ('sad', '😢 Sad'),
        ('angry', '😠 Angry'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    reaction = models.CharField(
        max_length=10,
        choices=REACTION_CHOICES,
        default='like'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('like')
        verbose_name_plural = _('likes')
        unique_together = ['user', 'post']  # User can like post only once
        indexes = [
            models.Index(fields=['post', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} reacted {self.reaction} on {self.post.id}"


class Comment(models.Model):
    """
    WHAT: Comments on posts with support for nested replies
    WHY: Users discuss posts, reply to each other
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Moderation
    is_edited = models.BooleanField(default=False)
    is_reported = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
        ordering = ['created_at']  # Oldest first for comments
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.id}"
    
    @property
    def is_reply(self):
        return self.parent is not None
    
    @property
    def reply_count(self):
        return self.replies.count()


class Share(models.Model):
    """
    WHAT: Post sharing functionality
    WHY: Users can share others' posts to their feed
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares')
    caption = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Add a caption (optional)')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('share')
        verbose_name_plural = _('shares')
        ordering = ['-created_at']
        unique_together = ['user', 'post']  # User can share post only once
    
    def __str__(self):
        return f"{self.user.username} shared {self.post.id}"


class SavedPost(models.Model):
    """
    WHAT: Bookmark/Save posts for later
    WHY: Users can save interesting posts
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('saved post')
        verbose_name_plural = _('saved posts')
        unique_together = ['user', 'post']  # Can't save same post twice
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.post.id}"


class Hashtag(models.Model):
    """
    WHAT: Hashtags for posts
    WHY: Posts ko categorize aur search karna easy ho
    """
    
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    post_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('hashtag')
        verbose_name_plural = _('hashtags')
        ordering = ['-post_count', 'name']
    
    def __str__(self):
        return f"#{self.name}"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('feed:hashtag', kwargs={'tag': self.name})


class Story(models.Model):
    """
    WHAT: Stories section - 24hr expiry images/videos
    WHY: User engagement, quick status sharing
    """
    
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='stories',
        verbose_name=_('author')
    )
    image = models.ImageField(
        _('image'),
        upload_to='stories/%Y/%m/',
        blank=True,
        null=True
    )
    video = models.FileField(
        _('video'),
        upload_to='stories/videos/%Y/%m/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('story')
        verbose_name_plural = _('stories')
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.author.username}'s story - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        
    @property
    def is_active(self):
        """Check if story is less than 24 hours old"""
        return self.created_at >= timezone.now() - timezone.timedelta(hours=24)