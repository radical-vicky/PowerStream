from django.db import models
from django.conf import settings
from django.urls import reverse
from hitcount.models import HitCount
from django.contrib.contenttypes.fields import GenericRelation
import os

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('videos:category', args=[self.slug])

class Video(models.Model):
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('unlisted', 'Unlisted'),
        ('private', 'Private'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='thumbnails/')
    video_file = models.FileField(upload_to='videos/')
    duration = models.DurationField(null=True, blank=True, help_text="Video duration in format HH:MM:SS")
    
    # Relationships
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='videos')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='videos')
    channel = models.ForeignKey('channels.Channel', on_delete=models.SET_NULL, null=True, blank=True, related_name='videos')
    
    # Stats
    views = GenericRelation(HitCount, object_id_field='object_pk', related_query_name='hit_count_generic_relation')
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    
    # Settings
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='public')
    allow_comments = models.BooleanField(default=True)
    allow_ratings = models.BooleanField(default=True)
    
    # SEO and Metadata
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags for SEO")
    allow_embed = models.BooleanField(default=True, help_text="Allow embedding on other sites")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['privacy', '-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('videos:detail', args=[self.id])
    
    def get_thumbnail_url(self):
        if self.thumbnail and hasattr(self.thumbnail, 'url'):
            return self.thumbnail.url
        return '/static/images/default-thumbnail.jpg'
    
    def get_video_url(self):
        if self.video_file and hasattr(self.video_file, 'url'):
            return self.video_file.url
        return ''
    
    def get_embed_url(self):
        """Get URL for embedding"""
        if self.allow_embed:
            return self.get_video_url()
        return ''
    
    @property
    def duration_seconds(self):
        """Return duration in seconds for schema.org"""
        if self.duration:
            return int(self.duration.total_seconds())
        return None
    
    @property
    def duration_iso(self):
        """Return duration in ISO 8601 format for schema.org video object"""
        if not self.duration:
            return None
        
        seconds = int(self.duration.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"PT{hours}H{minutes}M{secs}S"
        elif minutes > 0:
            return f"PT{minutes}M{secs}S"
        else:
            return f"PT{secs}S"
    
    @property
    def formatted_duration(self):
        """Return duration in readable format (MM:SS or HH:MM:SS)"""
        if not self.duration:
            return "0:00"
        
        seconds = int(self.duration.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    @property
    def privacy_color(self):
        colors = {
            'public': 'success',
            'unlisted': 'warning',
            'private': 'danger',
        }
        return colors.get(self.privacy, 'secondary')
    
    @property
    def privacy_icon(self):
        icons = {
            'public': 'globe',
            'unlisted': 'link',
            'private': 'lock',
        }
        return icons.get(self.privacy, 'question')
    
    @property
    def view_count(self):
        """Get total view count from hitcount"""
        return self.views.count()
    
    @property
    def is_public(self):
        """Check if video is publicly accessible"""
        return self.privacy == 'public'

class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'video')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} likes {self.video.title}"

class SuggestedPost(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='suggested_posts')
    channel = models.ForeignKey('channels.Channel', on_delete=models.CASCADE, related_name='suggested_posts')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Optional video file or external link
    video_file = models.FileField(upload_to='suggested_videos/', null=True, blank=True)
    external_link = models.URLField(max_length=500, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_suggestions')
    
    # Funding
    funding_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    funding_currency = models.CharField(max_length=10, default='USD')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Suggestion by {self.user.username} for {self.channel.name}: {self.title}"
    
    def get_preview_url(self):
        if self.video_file and hasattr(self.video_file, 'url'):
            return self.video_file.url
        return self.external_link