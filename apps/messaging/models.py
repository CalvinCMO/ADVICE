"""
apps/messaging/models.py
Messaging system: private conversations and in-app notifications.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Conversation(models.Model):

    CONV_DIRECT = 'direct'
    CONV_GROUP = 'group'
    CONV_SUPPORT = 'support'

    CONV_TYPES = [
        (CONV_DIRECT, 'Direct Message'),
        (CONV_GROUP, 'Group Chat'),
        (CONV_SUPPORT, 'Support Chat'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation_type = models.CharField(max_length=20, choices=CONV_TYPES, default=CONV_DIRECT)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='conversations',
        through='ConversationParticipant',
    )
    linked_session = models.ForeignKey(
        'counseling.CounselingSession', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='chat',
    )
    title = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation({self.id}) [{self.conversation_type}]"

    def get_last_message(self):
        return self.messages.filter(is_deleted=False).order_by('-sent_at').first()

    def unread_count_for(self, user):
        participant = self.conversationparticipant_set.filter(user=user).first()
        if not participant or not participant.last_read_at:
            return self.messages.exclude(sender=user).filter(is_deleted=False).count()
        return self.messages.exclude(sender=user).filter(
            is_deleted=False, sent_at__gt=participant.last_read_at
        ).count()

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()


class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['conversation', 'user']

    def mark_read(self):
        self.last_read_at = timezone.now()
        self.save(update_fields=['last_read_at'])


class Message(models.Model):

    MSG_TEXT = 'text'
    MSG_FILE = 'file'
    MSG_IMAGE = 'image'
    MSG_SYSTEM = 'system'

    MSG_TYPES = [
        (MSG_TEXT, 'Text'),
        (MSG_FILE, 'File'),
        (MSG_IMAGE, 'Image'),
        (MSG_SYSTEM, 'System Message'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='sent_messages',
    )
    message_type = models.CharField(max_length=20, choices=MSG_TYPES, default=MSG_TEXT)
    content = models.TextField()
    attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True)
    attachment_name = models.CharField(max_length=255, blank=True)

    is_flagged = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    sent_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['sent_at']

    def __str__(self):
        return f"[{self.sender}]: {self.content[:50]}"


class Notification(models.Model):

    NOTIF_SESSION_REMINDER = 'session_reminder'
    NOTIF_SESSION_CANCELLED = 'session_cancelled'
    NOTIF_SESSION_RESCHEDULED = 'session_rescheduled'
    NOTIF_NEW_MESSAGE = 'new_message'
    NOTIF_PROGRESS_UPDATE = 'progress_update'
    NOTIF_INVITATION = 'invitation'
    NOTIF_SYSTEM = 'system'
    NOTIF_CRISIS_ALERT = 'crisis_alert'
    NOTIF_GOAL = 'goal_update'

    NOTIF_TYPES = [
        (NOTIF_SESSION_REMINDER, 'Session Reminder'),
        (NOTIF_SESSION_CANCELLED, 'Session Cancelled'),
        (NOTIF_SESSION_RESCHEDULED, 'Session Rescheduled'),
        (NOTIF_NEW_MESSAGE, 'New Message'),
        (NOTIF_PROGRESS_UPDATE, 'Progress Update'),
        (NOTIF_INVITATION, 'Invitation'),
        (NOTIF_SYSTEM, 'System Notification'),
        (NOTIF_CRISIS_ALERT, 'Crisis Alert'),
        (NOTIF_GOAL, 'Goal Update'),
    ]

    ICON_MAP = {
        NOTIF_SESSION_REMINDER: '📅',
        NOTIF_SESSION_CANCELLED: '❌',
        NOTIF_SESSION_RESCHEDULED: '🔄',
        NOTIF_NEW_MESSAGE: '💬',
        NOTIF_PROGRESS_UPDATE: '📈',
        NOTIF_INVITATION: '✉️',
        NOTIF_SYSTEM: '🔔',
        NOTIF_CRISIS_ALERT: '🚨',
        NOTIF_GOAL: '🎯',
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications',
    )
    notification_type = models.CharField(max_length=30, choices=NOTIF_TYPES)
    title = models.CharField(max_length=200)
    body = models.TextField()
    action_url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    related_session_id = models.UUIDField(null=True, blank=True)
    related_message_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notif → {self.recipient.email}: {self.title}"

    def mark_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])

    @property
    def icon(self):
        return self.ICON_MAP.get(self.notification_type, '🔔')
