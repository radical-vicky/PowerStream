from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Video

class VideoSitemap(Sitemap):
    """Video sitemap for Google Video search"""
    changefreq = 'daily'
    priority = 0.5
    limit = 50000  # Google's limit per sitemap file [citation:1]

    def items(self):
        return Video.objects.filter(privacy='public').order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('videos:detail', args=[obj.pk])

    def get_video_data(self, obj):
        """
        Return video-specific data for Google Video sitemap.
        Follows Google's video sitemap schema [citation:8]
        """
        video_data = {
            'thumbnail_loc': obj.get_thumbnail_url(),  # Required
            'title': obj.title,  # Required
            'description': obj.description,  # Required
            'content_loc': obj.get_video_url(),  # Optional - direct video file
            'player_loc': obj.get_video_url(),  # Optional - embed player URL
            'duration': self._get_duration_seconds(obj),  # Optional - in seconds
            'publication_date': obj.created_at.isoformat(),  # Optional
            'family_friendly': 'yes',  # Optional
            'view_count': obj.views.count(),  # Optional
            'uploader': obj.user.username,  # Optional
            'uploader_info': reverse('users:profile', args=[obj.user.username]),  # Optional
        }
        return video_data

    def _get_duration_seconds(self, obj):
        """Convert duration to seconds if available"""
        if obj.duration:
            return int(obj.duration.total_seconds())
        return None