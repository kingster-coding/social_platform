"""
WHAT: Reels app models - Short videos like Instagram Reels
WHY: Video content sharing platform
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Reel(models.Model):
    """
    WHAT: Short video reel model
    WHY: Instagram-style vertical videos
    """
    
    PRIVACY_CHOICES = [
        ('public', _('Public')),
        ('followers', _('Followers Only')),
        ('private', _('Only Me')),
    ]
    
    # Basic Info
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reels'
    )
    
    title = models.CharField(
        _('title'),
        max_length=100,
        blank=True
    )
    
    caption = models.TextField(
        _('caption'),
        max_length=500,
        blank=True
    )
    
    # Video and Thumbnail
    video = models.FileField(
        _('video'),
        upload_to='reels/videos/%Y/%m/',
        help_text=_('Upload MP4 video (max 60 seconds)')
    )
    
    thumbnail = models.ImageField(
        _('thumbnail'),
        upload_to='reels/thumbnails/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Audio/Music
    audio_title = models.CharField(
        _('audio title'),
        max_length=200,
        blank=True,
        help_text=_('Background music/audio name')
    )
    
    audio_artist = models.CharField(
        _('audio artist'),
        max_length=100,
        blank=True
    )
    
    # Settings
    privacy = models.CharField(
        _('privacy'),
        max_length=10,
        choices=PRIVACY_CHOICES,
        default='public'
    )
    
    allow_comments = models.BooleanField(
        _('allow comments'),
        default=True
    )
    
    allow_duet = models.BooleanField(
        _('allow duet'),
        default=True
    )
    
    # Status
    is_draft = models.BooleanField(
        _('draft'),
        default=False
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    share_count = models.PositiveIntegerField(default=0)
    
    # Duration (in seconds)
    duration = models.PositiveIntegerField(
        default=0,
        help_text=_('Video duration in seconds')
    )
    
    class Meta:
        verbose_name = _('reel')
        verbose_name_plural = _('reels')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['view_count']),  # For trending
        ]
    
    def __str__(self):
        return f"{self.author.username}'s reel - {self.created_at.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        """Auto-set published_at when not draft"""
        if not self.is_draft and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def is_published(self):
        return not self.is_draft and self.published_at is not None
    
    def increment_view(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('reels:reel_detail', kwargs={'pk': self.pk})


class ReelLike(models.Model):
    """
    WHAT: Likes for reels
    WHY: User engagement tracking
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('reel like')
        verbose_name_plural = _('reel likes')
        unique_together = ['user', 'reel']
    
    def save(self, *args, **kwargs):
        """Update like_count on Reel"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.reel.like_count = self.reel.likes.count()
            self.reel.save(update_fields=['like_count'])
    
    def delete(self, *args, **kwargs):
        """Update like_count on Reel when unliked"""
        reel = self.reel
        super().delete(*args, **kwargs)
        reel.like_count = reel.likes.count()
        reel.save(update_fields=['like_count'])


class ReelComment(models.Model):
    """
    WHAT: Comments on reels
    WHY: User discussions on videos
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('reel comment')
        verbose_name_plural = _('reel comments')
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        """Update comment_count on Reel"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.reel.comment_count = self.reel.comments.count()
            self.reel.save(update_fields=['comment_count'])
    
    def delete(self, *args, **kwargs):
        """Update comment_count when comment deleted"""
        reel = self.reel
        super().delete(*args, **kwargs)
        reel.comment_count = reel.comments.count()
        reel.save(update_fields=['comment_count'])


class ReelShare(models.Model):
    """
    WHAT: Share tracking for reels
    WHY: Analytics and viral tracking
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='shares')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('reel share')
        verbose_name_plural = _('reel shares')
        unique_together = ['user', 'reel']
    
    def save(self, *args, **kwargs):
        """Update share_count on Reel"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.reel.share_count = self.reel.shares.count()
            self.reel.save(update_fields=['share_count'])


class ReelSave(models.Model):
    """
    WHAT: Save/bookmark reels
    WHY: Users can save reels for later
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_reels')
    reel = models.ForeignKey(Reel, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('saved reel')
        verbose_name_plural = _('saved reels')
        unique_together = ['user', 'reel']
        ordering = ['-created_at']