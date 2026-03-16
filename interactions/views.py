from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
import time
from decimal import Decimal, InvalidOperation
from .models import Tip
from videos.models import Video
from users.models import CustomUser

@login_required
def tip_user(request, username):
    recipient = get_object_or_404(CustomUser, username=username)
    video_id = request.GET.get('video')
    video = None
    if video_id:
        video = get_object_or_404(Video, id=video_id)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        message = request.POST.get('message', '')
        payment_method = request.POST.get('payment_method', 'card')
        
        try:
            amount = Decimal(amount)
            if amount < 1:
                messages.error(request, 'Minimum tip amount is $1.00')
                return redirect('interactions:tip', username=username)
            
            # Create tip record
            tip = Tip.objects.create(
                sender=request.user,
                recipient=recipient,
                amount=amount,
                message=message,
                payment_method=payment_method,
                video=video,
                transaction_id=f"TIP_{request.user.id}_{recipient.id}_{int(time.time())}"
            )
            
            # Update user stats - convert to Decimal for addition
            request.user.total_sent_tips += amount
            request.user.save(update_fields=['total_sent_tips'])
            
            recipient.total_received_tips += amount
            recipient.save(update_fields=['total_received_tips'])
            
            messages.success(request, f'Successfully sent ${amount} to {recipient.username}!')
            
            # Redirect to success page
            return redirect('interactions:tip_success', tip_id=tip.id)
            
        except (ValueError, InvalidOperation):
            messages.error(request, 'Invalid amount')
            return redirect('interactions:tip', username=username)
    
    context = {
        'recipient': recipient,
        'video': video,
    }
    return render(request, 'interactions/tip_form.html', context)

@login_required
def tip_success(request, tip_id):
    tip = get_object_or_404(Tip, id=tip_id, sender=request.user)
    
    context = {
        'tip': tip,
        'recipient': tip.recipient,
        'amount': tip.amount,
        'message': tip.message,
        'video': tip.video,
        'date': tip.created_at,
    }
    return render(request, 'interactions/tip_success.html', context)

@login_required
def tipping_history(request):
    # Tips sent
    sent_tips = Tip.objects.filter(sender=request.user).select_related('recipient', 'video').order_by('-created_at')
    sent_paginator = Paginator(sent_tips, 10)
    sent_page = request.GET.get('sent_page')
    sent_tips = sent_paginator.get_page(sent_page)
    
    # Tips received
    received_tips = Tip.objects.filter(recipient=request.user).select_related('sender', 'video').order_by('-created_at')
    received_paginator = Paginator(received_tips, 10)
    received_page = request.GET.get('received_page')
    received_tips = received_paginator.get_page(received_page)
    
    # Statistics
    total_sent = Tip.objects.filter(sender=request.user).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    total_received = Tip.objects.filter(recipient=request.user).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    
    # Withdrawable balance (80% of received tips after platform fee)
    withdrawable_balance = total_received * Decimal('0.8')
    
    # Count unique supporters
    supporters_count = Tip.objects.filter(recipient=request.user).values('sender').distinct().count()
    
    context = {
        'sent_tips': sent_tips,
        'received_tips': received_tips,
        'total_sent': total_sent,
        'total_received': total_received,
        'sent_count': sent_tips.paginator.count if sent_tips.paginator else sent_tips.count(),
        'received_count': received_tips.paginator.count if received_tips.paginator else received_tips.count(),
        'supporters_count': supporters_count,
        'withdrawable_balance': withdrawable_balance,
        'active_tab': request.GET.get('tab', 'sent'),
    }
    return render(request, 'interactions/tipping_history.html', context)