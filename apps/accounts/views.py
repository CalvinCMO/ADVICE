"""
apps/accounts/views.py
Authentication and user profile views.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
import uuid

from .models import User, InvitationCode
from .forms import (
    LoginForm, RegisterForm, ProfileUpdateForm,
    PasswordResetRequestForm, SetNewPasswordForm, NotificationPreferencesForm,
)
from apps.institutions.models import Institution


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        remember = form.cleaned_data.get('remember_me')

        try:
            user_obj = User.objects.get(email=email)
            if user_obj.is_locked:
                messages.error(request, f'Account locked due to too many failed attempts. Try again after {user_obj.locked_until.strftime("%H:%M")}.')
                return render(request, 'accounts/login.html', {'form': form})
        except User.DoesNotExist:
            user_obj = None

        user = authenticate(request, email=email, password=password)
        if user:
            if not user.is_active:
                messages.error(request, 'Your account has been deactivated.')
                return render(request, 'accounts/login.html', {'form': form})
            user.reset_failed_logins()
            login(request, user)
            user.update_last_activity()
            if not remember:
                request.session.set_expiry(0)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect(request.GET.get('next', 'dashboard'))
        else:
            if user_obj:
                user_obj.record_failed_login()
            messages.error(request, 'Invalid email or password.')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        invitation_code_str = form.cleaned_data.get('invitation_code', '').strip()
        institution = form.cleaned_data.get('institution')

        # Handle invitation code
        invite = None
        if invitation_code_str:
            try:
                invite = InvitationCode.objects.get(code=invitation_code_str)
                if not invite.is_valid:
                    messages.error(request, 'Invitation code is expired or already used.')
                    return render(request, 'accounts/register.html', {'form': form})
                institution = invite.institution
            except InvitationCode.DoesNotExist:
                messages.error(request, 'Invalid invitation code.')
                return render(request, 'accounts/register.html', {'form': form})

        user = form.save(commit=False)
        if institution:
            user.institution = institution
        user.email_verified = False
        user.save()

        if invite:
            invite.is_used = True
            invite.used_by = user
            invite.save()

        login(request, user)
        messages.success(request, f'Welcome to ADVICE, {user.first_name}! Your account has been created.')
        return redirect('dashboard')

    institutions = Institution.objects.filter(status='active')
    return render(request, 'accounts/register.html', {'form': form, 'institutions': institutions})


@login_required
def dashboard_view(request):
    """Route to role-specific dashboard."""
    user = request.user
    if user.is_super_admin:
        return redirect('admin_dashboard')
    elif user.is_institution_admin:
        return redirect('institution_dashboard')
    elif user.is_counselor:
        return redirect('counselor_dashboard')
    else:
        return redirect('student_dashboard')


@login_required
def profile_view(request):
    user = request.user
    form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
        elif new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
        elif len(new_password1) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')

    return render(request, 'accounts/change_password.html')


def password_reset_request_view(request):
    form = PasswordResetRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email, is_active=True)
            token = uuid.uuid4()
            user.password_reset_token = token
            user.password_reset_expires = timezone.now() + timezone.timedelta(hours=2)
            user.save(update_fields=['password_reset_token', 'password_reset_expires'])

            reset_url = request.build_absolute_uri(f'/password-reset/{token}/')
            send_mail(
                'Reset your ADVICE password',
                f'Click here to reset your password:\n{reset_url}\n\nThis link expires in 2 hours.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
        except User.DoesNotExist:
            pass
        messages.success(request, 'If an account exists with that email, a reset link has been sent.')
        return redirect('login')
    return render(request, 'accounts/password_reset.html', {'form': form})


def password_reset_confirm_view(request, token):
    try:
        user = User.objects.get(
            password_reset_token=token,
            password_reset_expires__gt=timezone.now(),
        )
    except User.DoesNotExist:
        messages.error(request, 'Invalid or expired reset link.')
        return redirect('password_reset')

    form = SetNewPasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user.set_password(form.cleaned_data['password1'])
        user.password_reset_token = None
        user.password_reset_expires = None
        user.save()
        messages.success(request, 'Password reset successful. You can now log in.')
        return redirect('login')

    return render(request, 'accounts/password_reset_confirm.html', {'form': form, 'token': token})


@login_required
def notification_preferences_view(request):
    form = NotificationPreferencesForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Notification preferences saved.')
        return redirect('profile')
    return render(request, 'accounts/notification_prefs.html', {'form': form})


# ── Admin user management ────────────────────────────────────────────────────

@login_required
def admin_dashboard_view(request):
    if not request.user.is_super_admin:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    from apps.institutions.models import Institution
    institutions = Institution.objects.all().order_by('-created_at')
    total_users = User.objects.count()
    total_institutions = institutions.count()
    active_institutions = institutions.filter(status='active').count()

    ctx = {
        'institutions': institutions[:10],
        'total_users': total_users,
        'total_institutions': total_institutions,
        'active_institutions': active_institutions,
    }
    return render(request, 'admin/super_dashboard.html', ctx)


@login_required
def institution_dashboard_view(request):
    if not (request.user.is_institution_admin or request.user.is_super_admin):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    institution = request.user.institution
    if not institution:
        messages.error(request, 'No institution associated with your account.')
        return redirect('home')

    members = User.objects.filter(institution=institution)
    students = members.filter(role=User.STUDENT)
    counselors = members.filter(role=User.COUNSELOR, is_verified=True)

    from apps.counseling.models import CounselingSession
    from apps.progress.models import CrisisAlert, WellnessCheck
    from django.utils import timezone
    from datetime import timedelta

    sessions_this_month = CounselingSession.objects.filter(
        counselor__institution=institution,
        scheduled_at__month=timezone.now().month,
        scheduled_at__year=timezone.now().year,
    )
    active_alerts = CrisisAlert.objects.filter(
        student__institution=institution, is_resolved=False
    ).select_related('student', 'counselor')

    ctx = {
        'institution': institution,
        'student_count': students.count(),
        'counselor_count': counselors.count(),
        'sessions_this_month': sessions_this_month.count(),
        'active_alerts': active_alerts[:5],
        'recent_members': members.order_by('-created_at')[:8],
    }
    return render(request, 'admin/institution_dashboard.html', ctx)


@login_required
def manage_users_view(request):
    if not (request.user.is_institution_admin or request.user.is_super_admin):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    institution = request.user.institution
    q = request.GET.get('q', '')
    role_filter = request.GET.get('role', '')

    users = User.objects.filter(institution=institution)
    if q:
        users = users.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
    if role_filter:
        users = users.filter(role=role_filter)

    return render(request, 'admin/manage_users.html', {
        'users': users.order_by('first_name'),
        'q': q,
        'role_filter': role_filter,
        'institution': institution,
    })


@login_required
def toggle_user_status_view(request, user_id):
    if not (request.user.is_institution_admin or request.user.is_super_admin):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    target = get_object_or_404(User, id=user_id, institution=request.user.institution)
    target.is_active = not target.is_active
    target.save(update_fields=['is_active'])
    status_str = 'activated' if target.is_active else 'deactivated'
    messages.success(request, f'{target.full_name} has been {status_str}.')
    return redirect('manage_users')


@login_required
def create_invitation_view(request):
    if not (request.user.is_institution_admin or request.user.is_super_admin):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', User.STUDENT)
        days = int(request.POST.get('days', 7))

        code = get_random_string(10).upper()
        InvitationCode.objects.create(
            code=code,
            email=email,
            role=role,
            institution=request.user.institution,
            created_by=request.user,
            expires_at=timezone.now() + timezone.timedelta(days=days),
        )

        send_mail(
            f'You\'re invited to join ADVICE',
            f'You have been invited to join {request.user.institution.name} on ADVICE.\n\nYour invitation code: {code}\n\nVisit {request.build_absolute_uri("/register/")} to get started.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=True,
        )
        messages.success(request, f'Invitation sent to {email}. Code: {code}')
        return redirect('manage_invitations')

    return render(request, 'admin/create_invitation.html', {
        'institution': request.user.institution,
        'roles': [(User.STUDENT, 'Student'), (User.COUNSELOR, 'Counselor')],
    })


@login_required
def manage_invitations_view(request):
    if not (request.user.is_institution_admin or request.user.is_super_admin):
        return redirect('dashboard')
    invitations = InvitationCode.objects.filter(
        institution=request.user.institution
    ).order_by('-created_at')
    return render(request, 'admin/manage_invitations.html', {'invitations': invitations})
