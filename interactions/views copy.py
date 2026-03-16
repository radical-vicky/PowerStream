from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from hitcount.views import HitCountDetailView
from .models import Video, Category, Like
from interactions.models import Comment, CommentLike, Share, Tip
from users.models import CustomUser

def video_list(request):
    videos = Video.objects.filter(privacy='public').select_related('user').prefetch_related('likes')
    
    # Search
    query = request.GET.get('q')
    if query:
        videos = videos.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(user__username__icontains=query)
        )
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        videos = videos.filter(category_id=category_id)
    
    # Sorting
    sort = request.GET.get('sort', '-created_at')
    if sort in ['created_at', '-created_at', 'likes_count', '-likes_count', 'views', '-views']:
        videos = videos.order_by(sort)
    
    paginator = Paginator(videos, 12)  # 12 videos per page
    page = request.GET.get('page')
    videos = paginator.get_page(page)
    
    categories = Category.objects.all()
    
    context = {
        'videos': videos,
        'categories': categories,
        'query': query,
    }
    return render(request, 'videos/video_list.html', context)

class VideoDetailView(HitCountDetailView):
    model = Video
    template_name = 'videos/video_detail.html'
    context_object_name = 'video'
    count_hit = True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = self.object
        
        # Get comments
        comments = Comment.objects.filter(video=video, parent=None).select_related('user').prefetch_related('replies')
        
        # Check if user liked the video
        if self.request.user.is_authenticated:
            context['user_liked'] = Like.objects.filter(user=self.request.user, video=video).exists()
        else:
            context['user_liked'] = False
        
        # Related videos
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
        thumbnail = request.FILES.get('thumbnail')
        video_file = request.FILES.get('video_file')
        privacy = request.POST.get('privacy', 'public')
        
        if title and description and thumbnail and video_file:
            video = Video.objects.create(
                title=title,
                description=description,
                category_id=category_id,
                thumbnail=thumbnail,
                video_file=video_file,
                user=request.user,
                privacy=privacy
            )
            messages.success(request, 'Video uploaded successfully!')
            return redirect('videos:detail', id=video.id)
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    categories = Category.objects.all()
    return render(request, 'videos/video_upload.html', {'categories': categories})

@login_required
def like_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    like, created = Like.objects.get_or_create(user=request.user, video=video)
    
    if not created:
        like.delete()
        video.likes_count -= 1
        video.user.total_likes -= 1
        messages.info(request, 'Video unliked.')
    else:
        video.likes_count += 1
        video.user.total_likes += 1
        messages.success(request, 'Video liked!')
    
    video.save()
    video.user.save()
    
    return redirect('videos:detail', id=video_id)

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
    
    return redirect('videos:detail', id=video_id)

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
    
    return redirect('videos:detail', id=video_id)

@login_required
def tip_user(request, username):
    recipient = get_object_or_404(CustomUser, username=username)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        message = request.POST.get('message', '')
        video_id = request.POST.get('video_id')
        
        # In a real app, you'd process payment here
        # For now, we'll just create a tip record
        
        tip = Tip.objects.create(
            sender=request.user,
            recipient=recipient,
            video_id=video_id,
            amount=amount,
            message=message,
            transaction_id=f"TXN_{request.user.id}_{recipient.id}_{int(time.time())}"
        )
        
        messages.success(request, f'You tipped ${amount} to {recipient.username}!')
        
        if video_id:
            return redirect('videos:detail', id=video_id)
        return redirect('users:profile', username=username)
    
    return render(request, 'interactions/tip_form.html', {'recipient': recipient})