"""
apps/counseling/models.py
Core counseling session management models.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class CounselingSession(models.Model):

    STATUS_SCHEDULED = 'scheduled'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_NO_SHOW = 'no_show'
    STATUS_RESCHEDULED = 'rescheduled'

    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_NO_SHOW, 'No Show'),
        (STATUS_RESCHEDULED, 'Rescheduled'),
    ]

    SESSION_INDIVIDUAL = 'individual'
    SESSION_GROUP = 'group'
    SESSION_CRISIS = 'crisis'

    SESSION_TYPES = [
        (SESSION_INDIVIDUAL, 'Individual Session'),
        (SESSION_GROUP, 'Group Session'),
        (SESSION_CRISIS, 'Crisis Intervention'),
    ]

    MODE_ONLINE = 'online'
    MODE_IN_PERSON = 'in_person'

    MODE_CHOICES = [
        (MODE_ONLINE, 'Online (Video/Chat)'),
        (MODE_IN_PERSON, 'In Person'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='sessions_as_student',
    )
    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='sessions_as_counselor',
    )

    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default=SESSION_INDIVIDUAL)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_ONLINE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)

    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    ended_at = models.DateTimeField(null=True, blank=True)

    reason = models.TextField(help_text='Reason for the session (student-provided)')
    agenda = models.TextField(blank=True)

    # Post-session (counselor only)
    counselor_notes = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_notes = models.TextField(blank=True)
    next_session_recommended = models.DateTimeField(null=True, blank=True)

    # Mood
    MOOD_CHOICES = [(i, str(i)) for i in range(1, 11)]
    student_mood_before = models.PositiveSmallIntegerField(null=True, blank=True, choices=MOOD_CHOICES)
    student_mood_after = models.PositiveSmallIntegerField(null=True, blank=True, choices=MOOD_CHOICES)

    # Cancellation
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='cancelled_sessions',
    )
    cancellation_reason = models.TextField(blank=True)

    # Video
    video_room_url = models.URLField(blank=True)
    meeting_id = models.CharField(max_length=100, blank=True)

    # Reminders
    reminder_sent_24h = models.BooleanField(default=False)
    reminder_sent_1h = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_at']
        verbose_name = 'Counseling Session'

    def __str__(self):
        return f"Session: {self.student.full_name} with {self.counselor.full_name} @ {self.scheduled_at:%Y-%m-%d %H:%M}"

    @property
    def is_upcoming(self):
        return self.status == self.STATUS_SCHEDULED and self.scheduled_at > timezone.now()

    @property
    def actual_duration(self):
        if self.ended_at:
            return int((self.ended_at - self.scheduled_at).total_seconds() / 60)
        return None

    def start(self):
        self.status = self.STATUS_IN_PROGRESS
        self.save(update_fields=['status'])

    def complete(self):
        self.status = self.STATUS_COMPLETED
        self.ended_at = timezone.now()
        self.save(update_fields=['status', 'ended_at'])


class GroupSession(models.Model):
    """Moderated group therapy/wellness session."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='facilitated_groups',
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='group_sessions',
        through='GroupSessionParticipant', blank=True,
    )
    max_participants = models.PositiveSmallIntegerField(default=15)
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=90)
    topic = models.CharField(max_length=200, blank=True)
    is_anonymous = models.BooleanField(default=False)
    is_open = models.BooleanField(default=True)
    meeting_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f"Group: {self.title} ({self.scheduled_at.date()})"

    @property
    def spots_remaining(self):
        return self.max_participants - self.participants.count()

    @property
    def is_full(self):
        return self.spots_remaining <= 0


class GroupSessionParticipant(models.Model):
    group_session = models.ForeignKey(GroupSession, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(null=True, blank=True)

    class Meta:
        unique_together = ['group_session', 'user']


class SessionFeedback(models.Model):
    """Student feedback after a completed session."""
    session = models.OneToOneField(CounselingSession, on_delete=models.CASCADE, related_name='feedback')
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    was_helpful = models.BooleanField()
    comments = models.TextField(blank=True)
    would_recommend = models.BooleanField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.session} — {self.rating}/5"


class CounselorAvailability(models.Model):
    """Recurring availability slots for a counselor."""
    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='availability_slots',
    )
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    day_of_week = models.SmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['counselor', 'day_of_week', 'start_time']
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.counselor.full_name}: {self.get_day_of_week_display()} {self.start_time}–{self.end_time}"
