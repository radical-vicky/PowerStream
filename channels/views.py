from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Channel
from videos.models import Video, SuggestedPost
from interactions.models import PostFunding
import uuid

def channel_list(request):
    """Display all public channels"""
    channels = Channel.objects.annotate(
        subscriber_count=Count('subscribers'),
        video_count=Count('videos')
    ).order_by('-subscriber_count', '-created_at')
    
    # Search
    query = request.GET.get('q')
    if query:
        channels = channels.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    paginator = Paginator(channels, 12)
    page = request.GET.get('page')
    channels_page = paginator.get_page(page)
    
    context = {
        'channels': channels_page,
        'query': query,
    }
    return render(request, 'channels/channel_list.html', context)

def channel_detail(request, slug):
    """Display channel details"""
    channel = get_object_or_404(Channel, slug=slug)
    
    # Get channel videos
    videos = Video.objects.filter(channel=channel).order_by('-created_at')
    
    # Check if user is subscribed
    is_subscribed = False
    if request.user.is_authenticated:
        is_subscribed = request.user in channel.subscribers.all()
    
    # Get pending suggestions (for owner)
    pending_suggestions = []
    if request.user.is_authenticated and request.user == channel.owner:
        pending_suggestions = SuggestedPost.objects.filter(
            channel=channel, 
            status='pending'
        ).order_by('-created_at')
    
    context = {
        'channel': channel,
        'videos': videos,
        'is_subscribed': is_subscribed,
        'pending_suggestions': pending_suggestions,
        'subscriber_count': channel.subscriber_count(),
    }
    return render(request, 'channels/channel_detail.html', context)

@login_required
def channel_create(request):
    """Create a new channel"""
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        is_private = request.POST.get('is_private') == 'on'
        
        if name and slug and description:
            # Check if slug is unique
            if Channel.objects.filter(slug=slug).exists():
                messages.error(request, 'This slug is already taken. Please choose another.')
            else:
                channel = Channel.objects.create(
                    name=name,
                    slug=slug,
                    description=description,
                    owner=request.user,
                    is_private=is_private
                )
                
                if 'avatar' in request.FILES:
                    channel.avatar = request.FILES['avatar']
                
                if 'cover_image' in request.FILES:
                    channel.cover_image = request.FILES['cover_image']
                
                channel.save()
                messages.success(request, f'Channel "{name}" created successfully!')
                return redirect('channels:detail', slug=channel.slug)
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return render(request, 'channels/channel_create.html')

@login_required
def channel_edit(request, slug):
    """Edit channel details"""
    channel = get_object_or_404(Channel, slug=slug)
    
    # Check if user is owner
    if channel.owner != request.user:
        messages.error(request, "You don't have permission to edit this channel.")
        return redirect('channels:detail', slug=channel.slug)
    
    if request.method == 'POST':
        channel.name = request.POST.get('name')
        channel.description = request.POST.get('description')
        channel.is_private = request.POST.get('is_private') == 'on'
        
        if 'avatar' in request.FILES:
            channel.avatar = request.FILES['avatar']
        
        if 'cover_image' in request.FILES:
            channel.cover_image = request.FILES['cover_image']
        
        channel.save()
        messages.success(request, 'Channel updated successfully!')
        return redirect('channels:detail', slug=channel.slug)
    
    context = {
        'channel': channel
    }
    return render(request, 'channels/channel_edit.html', context)

@login_required
def subscribe_channel(request, slug):
    """Subscribe to a channel"""
    channel = get_object_or_404(Channel, slug=slug)
    
    if request.user == channel.owner:
        messages.error(request, "You cannot subscribe to your own channel.")
        return redirect('channels:detail', slug=channel.slug)
    
    if request.user in channel.subscribers.all():
        # Unsubscribe
        channel.subscribers.remove(request.user)
        messages.info(request, f'Unsubscribed from {channel.name}')
    else:
        # Subscribe
        channel.subscribers.add(request.user)
        messages.success(request, f'Subscribed to {channel.name}!')
    
    return redirect('channels:detail', slug=channel.slug)

@login_required
def suggest_post(request, slug):
    """Suggest a post to a channel"""
    channel = get_object_or_404(Channel, slug=slug)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        funding_amount = request.POST.get('funding_amount')
        video_file = request.FILES.get('video_file')
        external_link = request.POST.get('external_link')
        
        if title and description:
            suggestion = SuggestedPost.objects.create(
                user=request.user,
                channel=channel,
                title=title,
                description=description,
                funding_amount=funding_amount if funding_amount else None
            )
            
            if video_file:
                suggestion.video_file = video_file
            elif external_link:
                suggestion.external_link = external_link
            
            suggestion.save()
            
            messages.success(
                request, 
                f'Your post has been suggested to {channel.name}! The channel owner will review it.'
            )
            return redirect('channels:detail', slug=channel.slug)
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    context = {
        'channel': channel
    }
    return render(request, 'channels/suggest_post.html', context)

@login_required
def review_suggestion(request, pk):
    """Review a suggested post (channel owner only)"""
    suggestion = get_object_or_404(SuggestedPost, pk=pk)
    channel = suggestion.channel
    
    # Check if user is channel owner
    if request.user != channel.owner:
        messages.error(request, "Only the channel owner can review suggestions.")
        return redirect('channels:detail', slug=channel.slug)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            # Create video from suggestion
            video = Video.objects.create(
                title=suggestion.title,
                description=suggestion.description,
                user=suggestion.user,  # Credit the suggester
                channel=channel,
                privacy='public'
            )
            
            if suggestion.video_file:
                video.video_file = suggestion.video_file
                video.save()
            
            suggestion.status = 'approved'
            suggestion.save()
            
            # Update channel video count
            channel.total_videos = Video.objects.filter(channel=channel).count()
            channel.save()
            
            messages.success(request, 'Suggestion approved and published!')
            
        elif action == 'reject':
            suggestion.status = 'rejected'
            suggestion.save()
            
            messages.info(request, 'Suggestion rejected.')
        
        return redirect('channels:detail', slug=channel.slug)
    
    context = {
        'suggestion': suggestion,
        'channel': channel
    }
    return render(request, 'channels/review_suggestion.html', context)

@login_required
def fund_suggestion(request, pk):
    """Fund a suggested post"""
    suggestion = get_object_or_404(SuggestedPost, pk=pk)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        funding_type = request.POST.get('funding_type', 'points')
        
        if amount and float(amount) > 0:
            # Create funding record
            funding = PostFunding.objects.create(
                suggested_post=suggestion,
                funder=request.user,
                amount=amount,
                funding_type=funding_type,
                transaction_id=f"FUND_{request.user.id}_{suggestion.id}_{uuid.uuid4().hex[:8]}"
            )
            
            # Update suggestion funding amount
            if suggestion.funding_amount:
                suggestion.funding_amount += float(amount)
            else:
                suggestion.funding_amount = float(amount)
            suggestion.save()
            
            messages.success(request, f'Thank you for funding this suggestion with ${amount}!')
        else:
            messages.error(request, 'Please enter a valid amount.')
    
    return redirect('channels:detail', slug=suggestion.channel.slug)


@login_required
def channel_delete(request, slug):
    """Delete a channel"""
    channel = get_object_or_404(Channel, slug=slug)
    
    # Check if user is owner
    if channel.owner != request.user:
        messages.error(request, "You don't have permission to delete this channel.")
        return redirect('channels:detail', slug=channel.slug)
    
    if request.method == 'POST':
        # Store channel name for success message
        channel_name = channel.name
        
        # Delete the channel
        channel.delete()
        messages.success(request, f'Channel "{channel_name}" has been deleted successfully.')
        return redirect('channels:list')
    
    # If not POST, redirect to edit page
    return redirect('channels:edit', slug=channel.slug)