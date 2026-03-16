from django.db import models
from django.conf import settings
from django.urls import reverse

class Channel(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    avatar = models.ImageField(upload_to='channel_avatars/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='channel_covers/', null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='channels_owned'  # Changed from 'owned_channels' to avoid conflict
    )
    subscribers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='channels_subscribed',  # Changed from 'subscribed_channels' to avoid conflict
        blank=True
    )
    is_private = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Stats
    total_videos = models.PositiveIntegerField(default=0)
    total_views = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('channels:detail', args=[self.slug])
    
    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return '/static/images/default-channel-avatar.png'
    
    def get_cover_url(self):
        if self.cover_image and hasattr(self.cover_image, 'url'):
            return self.cover_image.url
        return '/static/images/default-channel-cover.jpg'
    
    def subscriber_count(self):
        return self.subscribers.count()