"""
apps/institutions/views.py
Public-facing institution pages and home view.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Institution


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    institutions = Institution.objects.filter(status='active').order_by('name')
    return render(request, 'home.html', {'institutions': institutions})


def about_view(request):
    return render(request, 'about.html')


def contact_view(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you for your message. We\'ll be in touch soon.')
        return redirect('contact')
    return render(request, 'contact.html')


def privacy_view(request):
    return render(request, 'privacy.html')


def terms_view(request):
    return render(request, 'terms.html')


def institution_detail_view(request, slug):
    institution = get_object_or_404(Institution, slug=slug, status='active')
    return render(request, 'institutions/detail.html', {'institution': institution})


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler500(request):
    return render(request, '404.html', status=500)
