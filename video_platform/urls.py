from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import index, sitemap
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views
from videos.sitemaps import VideoSitemap

# Sitemaps configuration
sitemaps = {
    'videos': VideoSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.home, name='home'),
    path('accounts/', include('allauth.urls')),
    path('users/', include('users.urls')),
    path('videos/', include('videos.urls')),
    path('channels/', include('channels.urls')),
    path('chat/', include('chat.urls')),
    path('interactions/', include('interactions.urls')),
    path('ratings/', include('star_ratings.urls', namespace='ratings')),
    path('hitcount/', include('hitcount.urls', namespace='hitcount')),
    
    # Sitemap URLs - handles pagination automatically [citation:1]
    path('sitemap.xml', index, {'sitemaps': sitemaps}, name='sitemap-index'),
    path('sitemap-<section>.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap-section'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)