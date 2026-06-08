"""
apps/messaging/views.py
Messaging and notification views.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q

from .models import Conversation, ConversationParticipant, Message, Notification
from apps.accounts.models import User


@login_required
def conversations_view(request):
    user = request.user
    conversations = Conversation.objects.filter(
        participants=user, is_active=True
    ).prefetch_related('participants').order_by('-updated_at')

    conv_data = []
    for conv in conversations:
        last_msg = conv.get_last_message()
        other = conv.get_other_participant(user)
        conv_data.append({
            'conversation': conv,
            'last_message': last_msg,
            'other_user': other,
            'unread_count': conv.unread_count_for(user),
        })

    return render(request, 'messaging/conversations.html', {
        'conv_data': conv_data,
        'total_unread': sum(d['unread_count'] for d in conv_data),
    })


@login_required
def conversation_detail_view(request, conv_id):
    conv = get_object_or_404(Conversation, id=conv_id, participants=request.user)
    msgs = conv.messages.filter(is_deleted=False).select_related('sender').order_by('sent_at')

    # Mark as read
    participant = ConversationParticipant.objects.filter(
        conversation=conv, user=request.user
    ).first()
    if participant:
        participant.mark_read()

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            msg = Message.objects.create(
                conversation=conv,
                sender=request.user,
                content=content,
            )
            conv.updated_at = timezone.now()
            conv.save(update_fields=['updated_at'])

            # Notify other participant(s)
            for p in conv.participants.exclude(id=request.user.id):
                Notification.objects.create(
                    recipient=p,
                    notification_type=Notification.NOTIF_NEW_MESSAGE,
                    title=f'New message from {request.user.full_name}',
                    body=content[:100],
                    action_url=f'/messages/{conv.id}/',
                    related_message_id=msg.id,
                )
        return redirect('conversation_detail', conv_id=conv_id)

    other = conv.get_other_participant(request.user)
    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conv,
        'messages': msgs,
        'other_user': other,
    })


@login_required
def start_conversation_view(request):
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content', '').strip()

        try:
            recipient = User.objects.get(id=recipient_id, institution=request.user.institution)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('conversations')

        # Check for existing direct conversation
        existing = Conversation.objects.filter(
            participants=request.user,
            conversation_type='direct',
        ).filter(participants=recipient).first()

        if existing:
            conv = existing
        else:
            conv = Conversation.objects.create(conversation_type='direct')
            ConversationParticipant.objects.create(conversation=conv, user=request.user)
            ConversationParticipant.objects.create(conversation=conv, user=recipient)

        if content:
            Message.objects.create(conversation=conv, sender=request.user, content=content)
            conv.updated_at = timezone.now()
            conv.save(update_fields=['updated_at'])

            Notification.objects.create(
                recipient=recipient,
                notification_type=Notification.NOTIF_NEW_MESSAGE,
                title=f'New message from {request.user.full_name}',
                body=content[:100],
                action_url=f'/messages/{conv.id}/',
            )

        return redirect('conversation_detail', conv_id=conv.id)

    # GET: choose recipient
    if request.user.is_student:
        users = User.objects.filter(
            institution=request.user.institution,
            role=User.COUNSELOR,
            is_active=True,
        )
    else:
        users = User.objects.filter(
            institution=request.user.institution,
            is_active=True,
        ).exclude(id=request.user.id)

    return render(request, 'messaging/start_conversation.html', {'users': users})


@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'messaging/notifications.html', {'notifications': notifs})


@login_required
def mark_notification_read_view(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.mark_read()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    next_url = notif.action_url or 'notifications'
    return redirect(next_url)


@login_required
def mark_all_read_view(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications')
