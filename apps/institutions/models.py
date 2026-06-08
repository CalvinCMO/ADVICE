"""
apps/institutions/models.py
Institution model — represents a university or college on the platform.
"""

from django.db import models
from django.utils import timezone


class Institution(models.Model):

    PLAN_CHOICES = [
        ('starter', 'Starter'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
        ('trial', 'Free Trial'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('trial', 'Trial'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, default='Kenya')

    # Branding
    logo = models.ImageField(upload_to='institution_logos/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, default='#2563EB')
    secondary_color = models.CharField(max_length=7, default='#1E40AF')
    accent_color = models.CharField(max_length=7, default='#10B981')

    # Subscription
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='trial')
    plan_started_at = models.DateTimeField(null=True, blank=True)
    plan_expires_at = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')

    # Settings
    allow_student_self_registration = models.BooleanField(default=False)
    require_invitation_code = models.BooleanField(default=True)
    enable_peer_support = models.BooleanField(default=True)
    enable_group_sessions = models.BooleanField(default=True)
    max_session_duration_minutes = models.PositiveIntegerField(default=60)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Institution'
        verbose_name_plural = 'Institutions'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_plan_valid(self):
        if self.plan == 'enterprise':
            return True
        if self.plan_expires_at:
            return timezone.now() < self.plan_expires_at
        return False

    def get_student_count(self):
        return self.members.filter(role='student', is_active=True).count()

    def get_counselor_count(self):
        return self.members.filter(role='counselor', is_active=True).count()
