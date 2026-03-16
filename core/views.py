from django.shortcuts import render
from videos.models import Video, Category

def home(request):
    """Home page view"""
    featured_videos = Video.objects.filter(privacy='public').order_by('-created_at')[:8]
    categories = Category.objects.all()
    
    context = {
        'featured_videos': featured_videos,
        'categories': categories,
    }
    return render(request, 'core/home.html', context)