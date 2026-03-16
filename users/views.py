from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .models import Follow
from videos.models import Video
from chat.models import Conversation

User = get_user_model()

def profile(request, username):
    """Display user profile with followers and following"""
    user = get_object_or_404(User, username=username)
    
    # Get user's videos
    videos = Video.objects.filter(user=user, privacy='public').order_by('-created_at')
    
    # Check if current user follows this profile
    if request.user.is_authenticated:
        is_following = Follow.objects.filter(
            follower=request.user,
            following=user
        ).exists()
    else:
        is_following = False
    
    # Get followers and following counts
    followers_count = Follow.objects.filter(following=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    
    # Get followers and following lists (for dropdown)
    followers = Follow.objects.filter(following=user).select_related('follower')[:6]
    following = Follow.objects.filter(follower=user).select_related('following')[:6]
    
    # Check if there's an existing conversation
    conversation = None
    if request.user.is_authenticated and request.user != user:
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=user
        ).first()
    
    # Paginate videos
    paginator = Paginator(videos, 12)
    page = request.GET.get('page')
    videos = paginator.get_page(page)
    
    context = {
        'profile_user': user,
        'videos': videos,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
        'followers': followers,
        'following': following,
        'conversation': conversation,
    }
    return render(request, 'users/profile.html', context)

@login_required
def profile_edit(request, username):
    """Edit user profile"""
    if request.user.username != username:
        messages.error(request, "You can only edit your own profile.")
        return redirect('users:profile', username=username)
    
    if request.method == 'POST':
        user = request.user
        user.bio = request.POST.get('bio', '')
        user.location = request.POST.get('location', '')
        user.website = request.POST.get('website', '')
        
        # Handle birthday - convert empty string to None
        birthday = request.POST.get('birthday', '')
        if birthday:
            user.birthday = birthday
        else:
            user.birthday = None
            
        user.show_birthday = request.POST.get('show_birthday') == 'on'
        
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        
        if 'cover_image' in request.FILES:
            user.cover_image = request.FILES['cover_image']
        
        try:
            user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile', username=user.username)
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
    
    return render(request, 'users/profile_edit.html', {'profile_user': request.user})

@login_required
def follow_user(request, username):
    """Follow or unfollow a user"""
    user_to_follow = get_object_or_404(User, username=username)
    
    if request.user == user_to_follow:
        messages.error(request, "You cannot follow yourself.")
        return redirect('users:profile', username=username)
    
    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=user_to_follow
    )
    
    if created:
        user_to_follow.total_followers += 1
        request.user.total_following += 1
        user_to_follow.save()
        request.user.save()
        messages.success(request, f"You are now following {username}!")
    else:
        follow.delete()
        user_to_follow.total_followers -= 1
        request.user.total_following -= 1
        user_to_follow.save()
        request.user.save()
        messages.info(request, f"You unfollowed {username}.")
    
    return redirect('users:profile', username=username)

def followers_list(request, username):
    """Display list of followers"""
    user = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(following=user).select_related('follower')
    
    paginator = Paginator(followers, 20)
    page = request.GET.get('page')
    followers_page = paginator.get_page(page)
    
    context = {
        'profile_user': user,
        'followers': followers_page,
        'title': 'Followers'
    }
    return render(request, 'users/followers_list.html', context)

def following_list(request, username):
    """Display list of users being followed"""
    user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(follower=user).select_related('following')
    
    paginator = Paginator(following, 20)
    page = request.GET.get('page')
    following_page = paginator.get_page(page)
    
    context = {
        'profile_user': user,
        'following': following_page,
        'title': 'Following'
    }
    return render(request, 'users/following_list.html', context)