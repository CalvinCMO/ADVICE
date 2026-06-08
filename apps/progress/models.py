"""
apps/progress/models.py
Student mental health progress: wellness checks, goals, reports, crisis alerts.
"""

from django.db import models
from django.conf import settings
import uuid


class WellnessCheck(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wellness_checks',
    )

    mood_score = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 11)])
    anxiety_level = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 11)])
    sleep_quality = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 11)])
    energy_level = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 11)])
    stress_level = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 11)])
    social_connection = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 11)])

    notes = models.TextField(blank=True)
    triggers = models.JSONField(default=list, blank=True)
    coping_strategies_used = models.JSONField(default=list, blank=True)

    overall_score = models.FloatField(editable=False, default=0)

    flagged_for_review = models.BooleanField(default=False)
    reviewed_by_counselor = models.BooleanField(default=False)

    checked_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-checked_at']
        verbose_name = 'Wellness Check'
        unique_together = ['student', 'date']

    def __str__(self):
        return f"Wellness: {self.student.full_name} on {self.date} — score {self.overall_score}"

    def save(self, *args, **kwargs):
        self.overall_score = round((
            self.mood_score +
            (11 - self.anxiety_level) +
            self.sleep_quality +
            self.energy_level +
            (11 - self.stress_level) +
            self.social_connection
        ) / 6, 2)

        if self.mood_score <= 3 or self.anxiety_level >= 8 or self.stress_level >= 8:
            self.flagged_for_review = True

        super().save(*args, **kwargs)

    def mood_label(self):
        labels = {1: 'Very Low', 2: 'Very Low', 3: 'Low', 4: 'Below Average',
                  5: 'Average', 6: 'Above Average', 7: 'Good', 8: 'Good',
                  9: 'Excellent', 10: 'Excellent'}
        return labels.get(self.mood_score, 'Unknown')


class ProgressGoal(models.Model):

    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_ON_HOLD = 'on_hold'
    STATUS_ABANDONED = 'abandoned'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_ON_HOLD, 'On Hold'),
        (STATUS_ABANDONED, 'Abandoned'),
    ]

    CATEGORY_CHOICES = [
        ('academic', 'Academic Performance'),
        ('anxiety', 'Anxiety Management'),
        ('depression', 'Managing Depression'),
        ('social', 'Social Skills'),
        ('self_esteem', 'Self-Esteem'),
        ('stress', 'Stress Management'),
        ('relationships', 'Relationships'),
        ('career', 'Career & Purpose'),
        ('lifestyle', 'Healthy Lifestyle'),
        ('trauma', 'Trauma Processing'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals',
    )
    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='student_goals',
    )
    title = models.CharField(max_length=300)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='other')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    target_date = models.DateField(null=True, blank=True)
    progress_percentage = models.PositiveSmallIntegerField(default=0)

    milestones = models.JSONField(default=list, blank=True)
    counselor_notes = models.TextField(blank=True)
    student_reflection = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Goal: {self.title} ({self.student.full_name})"

    @property
    def progress_color(self):
        if self.progress_percentage >= 75:
            return 'green'
        elif self.progress_percentage >= 40:
            return 'yellow'
        return 'red'


class ProgressReport(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress_reports',
    )
    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='authored_reports',
    )
    report_period_start = models.DateField()
    report_period_end = models.DateField()
    summary = models.TextField()
    key_improvements = models.TextField(blank=True)
    areas_of_concern = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    next_steps = models.TextField(blank=True)

    avg_mood_score = models.FloatField(default=0)
    avg_wellness_score = models.FloatField(default=0)
    sessions_attended = models.PositiveSmallIntegerField(default=0)
    goals_completed = models.PositiveSmallIntegerField(default=0)

    shared_with_student = models.BooleanField(default=False)
    shared_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report: {self.student.full_name} ({self.report_period_start} – {self.report_period_end})"


class CrisisAlert(models.Model):

    SEVERITY_LOW = 'low'
    SEVERITY_MEDIUM = 'medium'
    SEVERITY_HIGH = 'high'
    SEVERITY_CRITICAL = 'critical'

    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical — Immediate Action Required'),
    ]

    SEVERITY_COLORS = {
        SEVERITY_LOW: 'yellow',
        SEVERITY_MEDIUM: 'orange',
        SEVERITY_HIGH: 'red',
        SEVERITY_CRITICAL: 'red',
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='crisis_alerts',
    )
    counselor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='crisis_alerts_received',
    )
    wellness_check = models.ForeignKey(
        WellnessCheck, on_delete=models.SET_NULL, null=True, blank=True, related_name='crisis_alert',
    )
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    trigger_reason = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"CrisisAlert [{self.severity}] → {self.student.full_name}"
