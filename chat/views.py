from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone  # Add this import
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()

@login_required
def inbox(request):
    """Display all conversations for the current user"""
    conversations = Conversation.objects.filter(
        participants=request.user
    ).prefetch_related(
        'participants', 'messages'
    ).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    ).order_by('-updated_at')
    
    context = {
        'conversations': conversations
    }
    return render(request, 'chat/inbox.html', context)

@login_required
def conversation_detail(request, conversation_id):
    """Display a specific conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    other_user = conversation.get_other_participant(request.user)
    
    # Mark messages as read
    Message.objects.filter(
        conversation=conversation, 
        sender=other_user,
        is_read=False
    ).update(is_read=True)
    
    messages_list = conversation.messages.all().order_by('created_at')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            conversation.updated_at = timezone.now()
            conversation.save()
            return redirect('chat:conversation', conversation_id=conversation.id)
    
    context = {
        'conversation': conversation,
        'other_user': other_user,
        'messages': messages_list
    }
    return render(request, 'chat/conversation.html', context)

@login_required
def start_conversation(request, username):
    """Start a new conversation with a user"""
    other_user = get_object_or_404(User, username=username)
    
    if other_user == request.user:
        messages.error(request, "You cannot start a conversation with yourself.")
        return redirect('users:profile', username=username)
    
    # Check if conversation already exists
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
        messages.success(request, f"Started a new conversation with {other_user.username}")
    
    return redirect('chat:conversation', conversation_id=conversation.id)

@login_required
def send_message_ajax(request, conversation_id):
    """AJAX endpoint for sending messages"""
    if request.method == 'POST':
        conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
        content = request.POST.get('content')
        
        if content:
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content
            )
            conversation.updated_at = timezone.now()
            conversation.save()
            
            return JsonResponse({
                'success': True,
                'message_id': message.id,
                'content': message.content,
                'created_at': message.created_at.strftime('%I:%M %p'),
                'sender': message.sender.username,
                'sender_avatar': message.sender.get_avatar_url(),
                'sender_name': message.sender.username
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def get_messages_ajax(request, conversation_id):
    """AJAX endpoint for getting new messages"""
    conversation = get_object_or_404(Conversation, id=conversation_id, participants=request.user)
    last_message_id = request.GET.get('last_message_id', 0)
    
    messages_list = conversation.messages.filter(
        id__gt=last_message_id
    ).order_by('created_at')
    
    # Mark received messages as read
    other_user = conversation.get_other_participant(request.user)
    messages_list.filter(sender=other_user).update(is_read=True)
    
    messages_data = []
    for msg in messages_list:
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'created_at': msg.created_at.strftime('%I:%M %p'),
            'sender': msg.sender.username,
            'sender_avatar': msg.sender.get_avatar_url(),
            'sender_name': msg.sender.username,
            'is_me': msg.sender == request.user
        })
    
    return JsonResponse({
        'success': True,
        'messages': messages_data,
        'has_more': False
    })

@login_required
def get_unread_count(request):
    """AJAX endpoint for getting unread message count"""
    conversations = Conversation.objects.filter(participants=request.user)
    unread_count = 0
    
    for conv in conversations:
        other_user = conv.get_other_participant(request.user)
        if other_user:
            unread_count += Message.objects.filter(
                conversation=conv,
                sender=other_user,
                is_read=False
            ).count()
    
    return JsonResponse({'unread_count': unread_count})