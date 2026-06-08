"""
apps/payments/views.py
Subscription and billing views.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import SubscriptionPlan, InstitutionSubscription, PaymentRecord


@login_required
def billing_view(request):
    if not (request.user.is_institution_admin or request.user.is_super_admin):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    institution = request.user.institution
    subscription = None
    payments = []

    try:
        subscription = InstitutionSubscription.objects.get(institution=institution)
        payments = PaymentRecord.objects.filter(institution=institution).order_by('-created_at')[:20]
    except InstitutionSubscription.DoesNotExist:
        pass

    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order')

    return render(request, 'payments/billing.html', {
        'institution': institution,
        'subscription': subscription,
        'payments': payments,
        'plans': plans,
    })


def plans_view(request):
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order')
    return render(request, 'payments/plans.html', {'plans': plans})
