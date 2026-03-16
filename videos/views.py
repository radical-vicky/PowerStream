from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, OuterRef, Subquery
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.http import JsonResponse, Http404 
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from hitcount.views import HitCountDetailView
from hitcount.models import HitCount
from django.contrib.contenttypes.models import ContentType
from .models import Video, Category, Like
from interactions.models import Comment, Share
from datetime import timedelta
import os

def video_list(request):
    videos = Video.objects.filter(privacy='public').select_related('user').prefetch_related('likes')
    
    query = request.GET.get('q')
    if query:
        videos = videos.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(user__username__icontains=query)
        )
    
    category_id = request.GET.get('category')
    if category_id:
        videos = videos.filter(category_id=category_id)
    
    sort = request.GET.get('sort', '-created_at')
    if sort in ['created_at', '-created_at', 'likes_count', '-likes_count']:
        videos = videos.order_by(sort)
    elif sort == 'most_viewed':
        # Annotate with view count from HitCount
        content_type = ContentType.objects.get_for_model(Video)
        hitcount_subquery = HitCount.objects.filter(
            content_type=content_type,
            object_pk=OuterRef('pk')
        ).values('hits')[:1]
        videos = videos.annotate(view_count=Subquery(hitcount_subquery)).order_by('-view_count')
    
    paginator = Paginator(videos, 12)
    page = request.GET.get('page')
    videos = paginator.get_page(page)
    
    categories = Category.objects.all()
    
    context = {
        'videos': videos,
        'categories': categories,
        'query': query,
        'sort': sort,
    }
    return render(request, 'videos/video_list.html', context)


class VideoDetailView(HitCountDetailView):
    model = Video
    template_name = 'videos/video_detail.html'
    context_object_name = 'video'
    count_hit = True
    pk_url_kwarg = 'pk'
    
    def get_object(self, queryset=None):
        try:
            video = super().get_object(queryset)
            return video
        except Http404:
            return None
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            return render(request, 'videos/video_not_found.html', status=404)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = self.object
        
        comments = Comment.objects.filter(video=video, parent=None).select_related('user').prefetch_related('replies')
        
        if self.request.user.is_authenticated:
            context['user_liked'] = Like.objects.filter(user=self.request.user, video=video).exists()
        else:
            context['user_liked'] = False
        
        context['related_videos'] = Video.objects.filter(
            category=video.category, 
            privacy='public'
        ).exclude(id=video.id)[:6]
        
        context['comments'] = comments
        return context


@login_required
def video_upload(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        channel_id = request.POST.get('channel')
        thumbnail = request.FILES.get('thumbnail')
        video_file = request.FILES.get('video_file')
        privacy = request.POST.get('privacy', 'public')
        
        if title and description and thumbnail and video_file:
            video = Video.objects.create(
                title=title,
                description=description,
                category_id=category_id,
                channel_id=channel_id if channel_id else None,
                thumbnail=thumbnail,
                video_file=video_file,
                user=request.user,
                privacy=privacy
            )
            
            # Update channel video count
            if video.channel:
                video.channel.total_videos = Video.objects.filter(channel=video.channel).count()
                video.channel.save()
            
            messages.success(request, 'Video uploaded successfully!')
            return redirect('videos:detail', pk=video.id)
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    categories = Category.objects.all()
    user_channels = request.user.channels_owned.all() if request.user.is_authenticated else []
    
    context = {
        'categories': categories,
        'user_channels': user_channels,
    }
    return render(request, 'videos/video_upload.html', context)


@login_required
def video_edit(request, pk):
    video = get_object_or_404(Video, pk=pk)
    
    if video.user != request.user:
        messages.error(request, "You don't have permission to edit this video.")
        return redirect('videos:detail', pk=video.pk)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        channel_id = request.POST.get('channel')
        privacy = request.POST.get('privacy', 'public')
        
        if title and description:
            # Store old channel for count update
            old_channel = video.channel
            
            video.title = title
            video.description = description
            video.category_id = category_id
            video.channel_id = channel_id if channel_id else None
            video.privacy = privacy
            
            if 'thumbnail' in request.FILES:
                if video.thumbnail and os.path.isfile(video.thumbnail.path):
                    os.remove(video.thumbnail.path)
                video.thumbnail = request.FILES['thumbnail']
            
            video.save()
            
            # Update channel video counts
            if old_channel:
                old_channel.total_videos = Video.objects.filter(channel=old_channel).count()
                old_channel.save()
            
            if video.channel:
                video.channel.total_videos = Video.objects.filter(channel=video.channel).count()
                video.channel.save()
            
            messages.success(request, 'Video updated successfully!')
            return redirect('videos:detail', pk=video.pk)
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    categories = Category.objects.all()
    user_channels = request.user.channels_owned.all()
    
    context = {
        'video': video,
        'categories': categories,
        'user_channels': user_channels,
    }
    return render(request, 'videos/video_edit.html', context)


@login_required
def video_delete(request, pk):
    video = get_object_or_404(Video, pk=pk)
    
    if video.user != request.user:
        messages.error(request, "You don't have permission to delete this video.")
        return redirect('videos:detail', pk=video.pk)
    
    if request.method == 'POST':
        # Store channel for count update
        channel = video.channel
        
        # Delete files from storage
        if video.thumbnail and os.path.isfile(video.thumbnail.path):
            os.remove(video.thumbnail.path)
        
        if video.video_file and os.path.isfile(video.video_file.path):
            os.remove(video.video_file.path)
        
        video.delete()
        
        # Update channel video count
        if channel:
            channel.total_videos = Video.objects.filter(channel=channel).count()
            channel.save()
        
        messages.success(request, 'Video deleted successfully!')
        return redirect('videos:list')
    
    return render(request, 'videos/video_delete_confirm.html', {'video': video})


@login_required
def like_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    
    like, created = Like.objects.get_or_create(user=request.user, video=video)
    
    if not created:
        like.delete()
        video.likes_count -= 1
        video.user.total_likes -= 1
        liked = False
        message = 'Video unliked.'
    else:
        video.likes_count += 1
        video.user.total_likes += 1
        liked = True
        message = 'Video liked!'
    
    video.save()
    video.user.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': video.likes_count,
            'message': message
        })
    
    messages.success(request, message)
    return redirect('videos:detail', pk=video_id)


@login_required
def add_comment(request, video_id):
    if request.method == 'POST':
        video = get_object_or_404(Video, id=video_id)
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        
        if content:
            comment = Comment.objects.create(
                user=request.user,
                video=video,
                content=content,
                parent_id=parent_id
            )
            video.comments_count += 1
            video.save()
            messages.success(request, 'Comment added!')
    
    return redirect('videos:detail', pk=video_id)


@login_required
def share_video(request, video_id):
    if request.method == 'POST':
        video = get_object_or_404(Video, id=video_id)
        platform = request.POST.get('platform')
        
        share = Share.objects.create(
            user=request.user,
            video=video,
            platform=platform
        )
        
        video.shares_count += 1
        video.save()
        messages.success(request, f'Video shared on {platform}!')
    
    return redirect('videos:detail', pk=video_id)

@login_required
def my_videos(request):
    # Get user's videos
    from django.contrib.contenttypes.models import ContentType
    from hitcount.models import HitCount
    from django.db.models import OuterRef, Subquery, IntegerField
    from django.db.models.functions import Coalesce
    
    user_videos = Video.objects.filter(user=request.user)
    
    # Calculate statistics
    total_videos = user_videos.count()
    
    # Get content type for Video model
    content_type = ContentType.objects.get_for_model(Video)
    
    # Get total views from HitCount for all user's videos
    video_ids = user_videos.values_list('id', flat=True)
    total_views = HitCount.objects.filter(
        content_type=content_type,
        object_pk__in=video_ids
    ).aggregate(
        total=Coalesce(Sum('hits'), 0)
    )['total']
    
    # Total likes
    total_likes = user_videos.aggregate(
        total=Coalesce(Sum('likes_count'), 0)
    )['total']
    
    # Total hours
    total_duration = user_videos.aggregate(
        total=Coalesce(Sum('duration'), timedelta(seconds=0))
    )['total']
    
    # Convert to hours
    if total_duration:
        total_hours = round(total_duration.total_seconds() / 3600, 1)
    else:
        total_hours = 0
    
    # Annotate each video with its view count from HitCount
    # Use a different name than 'view_count' to avoid conflict with the property
    hitcount_subquery = HitCount.objects.filter(
        content_type=content_type,
        object_pk=OuterRef('pk')
    ).values('hits')[:1]
    
    # Annotate with a proper integer field - using 'total_views' instead of 'view_count'
    user_videos = user_videos.annotate(
        video_views=Coalesce(Subquery(hitcount_subquery, output_field=IntegerField()), 0)
    )
    
    # Handle sorting
    sort = request.GET.get('sort', 'newest')
    if sort == 'oldest':
        user_videos = user_videos.order_by('created_at')
    elif sort == 'most_viewed':
        user_videos = user_videos.order_by('-video_views')
    elif sort == 'most_liked':
        user_videos = user_videos.order_by('-likes_count')
    else:  # newest
        user_videos = user_videos.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(user_videos, 12)
    page = request.GET.get('page')
    videos = paginator.get_page(page)
    
    context = {
        'videos': videos,
        'total_videos': total_videos,
        'total_views': total_views,
        'total_likes': total_likes,
        'total_hours': total_hours,
        'sort': sort,
    }
    return render(request, 'videos/my_videos.html', context)

@login_required
def liked_videos(request):
    from django.contrib.contenttypes.models import ContentType
    from hitcount.models import HitCount
    from django.db.models import OuterRef, Subquery, IntegerField
    from django.db.models.functions import Coalesce
    
    liked_videos = Video.objects.filter(likes__user=request.user).order_by('-likes__created_at')
    
    # Get content type for Video model
    content_type = ContentType.objects.get_for_model(Video)
    
    # Annotate each video with its view count from HitCount
    # Use a different name than 'view_count' to avoid conflict with the property
    hitcount_subquery = HitCount.objects.filter(
        content_type=content_type,
        object_pk=OuterRef('pk')
    ).values('hits')[:1]
    
    liked_videos = liked_videos.annotate(
        video_views=Coalesce(Subquery(hitcount_subquery, output_field=IntegerField()), 0)
    )
    
    # Calculate statistics for liked videos
    total_liked_videos = liked_videos.count()
    
    # Get total views from HitCount for all liked videos
    video_ids = liked_videos.values_list('id', flat=True)
    total_views = HitCount.objects.filter(
        content_type=content_type,
        object_pk__in=video_ids
    ).aggregate(
        total=Coalesce(Sum('hits'), 0)
    )['total']
    
    # Calculate total hours (if you have duration field)
    total_duration = liked_videos.aggregate(
        total=Coalesce(Sum('duration'), timedelta(seconds=0))
    )['total']
    
    # Convert to hours
    if total_duration:
        total_hours = round(total_duration.total_seconds() / 3600, 1)
    else:
        total_hours = 0
    
    # Handle sorting
    sort = request.GET.get('sort', 'recent')
    if sort == 'oldest':
        liked_videos = liked_videos.order_by('likes__created_at')
    elif sort == 'most_viewed':
        liked_videos = liked_videos.order_by('-video_views')
    elif sort == 'most_liked':
        liked_videos = liked_videos.order_by('-likes_count')
    else:  # recent
        liked_videos = liked_videos.order_by('-likes__created_at')
    
    # Pagination
    paginator = Paginator(liked_videos, 12)
    page = request.GET.get('page')
    videos = paginator.get_page(page)
    
    context = {
        'videos': videos,
        'total_liked_videos': total_liked_videos,
        'total_views': total_views,
        'total_hours': total_hours,
        'sort': sort,
    }
    return render(request, 'videos/liked_videos.html', context)