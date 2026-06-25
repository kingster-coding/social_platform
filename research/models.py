"""
WHAT: Research Papers app models
WHY: Academic paper sharing platform like ResearchGate
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class ResearchCategory(models.Model):
    """
    WHAT: Categories for research papers
    WHY: Organize papers by field
    """
    
    name = models.CharField(_('category name'), max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text=_('Font Awesome icon name'))
    
    class Meta:
        verbose_name = _('research category')
        verbose_name_plural = _('research categories')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ResearchPaper(models.Model):
    """
    WHAT: Main research paper model
    WHY: Upload and share academic papers
    """
    
    ACCESS_CHOICES = [
        ('public', _('Public')),
        ('registered', _('Registered Users Only')),
        ('private', _('Private')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('submitted', _('Submitted for Review')),
        ('under_review', _('Under Review')),
        ('published', _('Published')),
        ('rejected', _('Rejected')),
    ]
    
    # Basic Info
    title = models.CharField(_('title'), max_length=300)
    abstract = models.TextField(_('abstract'), max_length=2000)
    keywords = models.CharField(_('keywords'), max_length=500, help_text=_('Comma separated keywords'))
    
    # Authors
    primary_author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='primary_papers',
        verbose_name=_('primary author')
    )
    
    co_authors = models.ManyToManyField(
        User,
        related_name='co_authored_papers',
        blank=True,
        verbose_name=_('co-authors')
    )
    
    additional_authors = models.TextField(
        _('additional authors'),
        blank=True,
        help_text=_('Authors not on platform (Name; Institution)')
    )
    
    # Paper File
    file = models.FileField(
        _('paper file'),
        upload_to='research/papers/%Y/%m/',
        help_text=_('Upload PDF file')
    )
    
    cover_image = models.ImageField(
        _('cover image'),
        upload_to='research/covers/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Metadata
    doi = models.CharField(
        _('DOI'),
        max_length=100,
        blank=True,
        unique=True,
        help_text=_('Digital Object Identifier (if published)')
    )
    
    journal_name = models.CharField(
        _('journal/conference name'),
        max_length=200,
        blank=True
    )
    
    publication_date = models.DateField(
        _('publication date'),
        null=True,
        blank=True
    )
    
    volume = models.CharField(max_length=50, blank=True)
    issue = models.CharField(max_length=50, blank=True)
    pages = models.CharField(max_length=50, blank=True)
    
    # Categorization
    category = models.ForeignKey(
        ResearchCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='papers'
    )
    
    # Settings
    access_level = models.CharField(
        _('access level'),
        max_length=15,
        choices=ACCESS_CHOICES,
        default='public'
    )
    
    status = models.CharField(
        _('status'),
        max_length=15,
        choices=STATUS_CHOICES,
        default='published'
    )
    
    allow_comments = models.BooleanField(default=True)
    allow_download = models.BooleanField(default=True)
    
    # Version Control
    version = models.PositiveIntegerField(default=1)
    previous_version = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newer_versions'
    )
    
    version_notes = models.TextField(blank=True, help_text=_('What changed in this version?'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    citation_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('research paper')
        verbose_name_plural = _('research papers')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['title']),
            models.Index(fields=['primary_author', '-created_at']),
            models.Index(fields=['category', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def author_list(self):
        """Get formatted author list"""
        authors = [self.primary_author.get_full_name()]
        authors.extend([co.get_full_name() for co in self.co_authors.all()])
        if self.additional_authors:
            authors.extend([a.strip() for a in self.additional_authors.split(';')])
        return authors
    
    def get_citation_apa(self):
        """Generate APA 7th edition citation"""
        authors = ', '.join(self.author_list)
        year = self.publication_date.year if self.publication_date else self.created_at.year
        return f"{authors} ({year}). {self.title}. {self.journal_name or 'Unpublished'}."
    
    def get_citation_mla(self):
        """Generate MLA 9th edition citation"""
        authors = ' and '.join(self.author_list)
        year = self.publication_date.year if self.publication_date else self.created_at.year
        return f"{authors}. \"{self.title}.\" {self.journal_name or 'Unpublished'}, {year}."
    
    def get_citation_chicago(self):
        """Generate Chicago style citation"""
        authors = ', '.join(self.author_list)
        year = self.publication_date.year if self.publication_date else self.created_at.year
        return f"{authors}. \"{self.title}.\" {self.journal_name or 'Unpublished'} ({year})."
    
    def get_citation_bibtex(self):
        """Generate BibTeX citation"""
        first_author = self.primary_author.last_name or self.primary_author.username
        year = self.publication_date.year if self.publication_date else self.created_at.year
        cite_key = f"{first_author}{year}{self.title[:20].replace(' ', '')}"
        
        return f"""@article{{{cite_key},
    author = {{{' and '.join(self.author_list)}}},
    title = {{{self.title}}},
    journal = {{{self.journal_name or 'Unpublished'}}},
    year = {{{year}}},
    doi = {{{self.doi or ''}}}
}}"""
    
    def increment_view(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_download(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])


class PaperComment(models.Model):
    """
    WHAT: Comments/Peer reviews on papers
    WHY: Academic discussion and peer review
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    paper = models.ForeignKey(ResearchPaper, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=1000)
    is_review = models.BooleanField(default=False, help_text=_('Is this a formal peer review?'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('paper comment')
        verbose_name_plural = _('paper comments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.paper.title}"


class PaperLike(models.Model):
    """
    WHAT: Likes/Recommendations for papers
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    paper = models.ForeignKey(ResearchPaper, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('paper like')
        verbose_name_plural = _('paper likes')
        unique_together = ['user', 'paper']


class PaperSave(models.Model):
    """
    WHAT: Save/bookmark papers
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_papers')
    paper = models.ForeignKey(ResearchPaper, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('saved paper')
        verbose_name_plural = _('saved papers')
        unique_together = ['user', 'paper']


class ResearcherFollow(models.Model):
    """
    WHAT: Follow researchers
    WHY: Get updates on new papers
    """
    
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_researchers')
    researcher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers_list')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('researcher follow')
        verbose_name_plural = _('researcher follows')
        unique_together = ['follower', 'researcher']