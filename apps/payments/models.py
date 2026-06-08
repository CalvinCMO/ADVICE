"""
apps/payments/models.py
Subscription and payment management.
"""

from django.db import models
from django.utils import timezone
import uuid


class SubscriptionPlan(models.Model):

    BILLING_MONTHLY = 'monthly'
    BILLING_ANNUAL = 'annual'
    BILLING_CYCLES = [(BILLING_MONTHLY, 'Monthly'), (BILLING_ANNUAL, 'Annual')]

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default=BILLING_ANNUAL)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_student_usd = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    max_students = models.PositiveIntegerField(null=True, blank=True)
    max_counselors = models.PositiveIntegerField(null=True, blank=True)
    max_sessions_per_month = models.PositiveIntegerField(null=True, blank=True)

    has_real_time_chat = models.BooleanField(default=True)
    has_group_sessions = models.BooleanField(default=True)
    has_peer_support = models.BooleanField(default=False)
    has_analytics = models.BooleanField(default=True)
    has_custom_branding = models.BooleanField(default=False)
    has_api_access = models.BooleanField(default=False)
    has_priority_support = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.name} ({self.billing_cycle})"


class InstitutionSubscription(models.Model):

    STATUS_ACTIVE = 'active'
    STATUS_PAST_DUE = 'past_due'
    STATUS_CANCELLED = 'cancelled'
    STATUS_TRIALING = 'trialing'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_PAST_DUE, 'Past Due'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_TRIALING, 'Trialing'),
    ]

    institution = models.OneToOneField(
        'institutions.Institution', on_delete=models.CASCADE, related_name='subscription',
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TRIALING)

    started_at = models.DateTimeField(default=timezone.now)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)

    student_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Institution Subscription'

    def __str__(self):
        return f"Subscription({self.institution.name}) — {self.plan.name}"

    @property
    def is_active(self):
        return self.status in [self.STATUS_ACTIVE, self.STATUS_TRIALING]


class PaymentRecord(models.Model):

    GATEWAY_STRIPE = 'stripe'
    GATEWAY_PAYPAL = 'paypal'
    GATEWAY_MANUAL = 'manual'
    GATEWAYS = [
        (GATEWAY_STRIPE, 'Stripe'),
        (GATEWAY_PAYPAL, 'PayPal'),
        (GATEWAY_MANUAL, 'Manual / Invoice'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'succeeded'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'
    STATUSES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESS, 'Succeeded'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        InstitutionSubscription, on_delete=models.SET_NULL, null=True, related_name='payments',
    )
    institution = models.ForeignKey(
        'institutions.Institution', on_delete=models.CASCADE, related_name='payments',
    )
    gateway = models.CharField(max_length=20, choices=GATEWAYS)
    gateway_payment_id = models.CharField(max_length=200, blank=True)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='USD')
    status = models.CharField(max_length=20, choices=STATUSES, default=STATUS_PENDING)
    description = models.CharField(max_length=300, blank=True)
    failure_reason = models.TextField(blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment ${self.amount_usd} [{self.status}] via {self.gateway}"
