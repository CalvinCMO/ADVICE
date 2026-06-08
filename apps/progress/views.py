"""
apps/progress/views.py
Wellness check-ins, goal tracking, progress reports, crisis management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count
from datetime import timedelta, date

from .models import WellnessCheck, ProgressGoal, ProgressReport, CrisisAlert
from apps.accounts.models import User
from apps.messaging.models import Notification


# ── Wellness ─────────────────────────────────────────────────────────────────

@login_required
def wellness_view(request):
    user = request.user
    today = timezone.now().date()
    already_checked_in = WellnessCheck.objects.filter(student=user, date=today).exists()

    recent = WellnessCheck.objects.filter(student=user).order_by('-date')[:30]

    # Trend data for the chart (last 14 days)
    trend = list(
        WellnessCheck.objects.filter(student=user, date__gte=today - timedelta(days=14))
        .order_by('date')
        .values('date', 'mood_score', 'anxiety_level', 'sleep_quality', 'overall_score')
    )

    avg_mood = sum(w['mood_score'] for w in trend) / len(trend) if trend else 0
    avg_wellness = sum(w['overall_score'] for w in trend) / len(trend) if trend else 0

    return render(request, 'progress/wellness.html', {
        'already_checked_in': already_checked_in,
        'recent_checks': recent,
        'trend': trend,
        'avg_mood': round(avg_mood, 1),
        'avg_wellness': round(avg_wellness, 1),
    })


@login_required
def wellness_checkin_view(request):
    if not request.user.is_student:
        return redirect('dashboard')

    today = timezone.now().date()
    if WellnessCheck.objects.filter(student=request.user, date=today).exists():
        messages.info(request, 'You have already submitted a wellness check-in today.')
        return redirect('wellness')

    if request.method == 'POST':
        try:
            check = WellnessCheck.objects.create(
                student=request.user,
                mood_score=int(request.POST.get('mood_score', 5)),
                anxiety_level=int(request.POST.get('anxiety_level', 5)),
                sleep_quality=int(request.POST.get('sleep_quality', 5)),
                energy_level=int(request.POST.get('energy_level', 5)),
                stress_level=int(request.POST.get('stress_level', 5)),
                social_connection=int(request.POST.get('social_connection', 5)),
                notes=request.POST.get('notes', ''),
                triggers=request.POST.getlist('triggers'),
            )

            if check.flagged_for_review:
                # Notify counselor if student has one
                from apps.counseling.models import CounselingSession
                recent_counselor = CounselingSession.objects.filter(
                    student=request.user, status='completed'
                ).order_by('-scheduled_at').values_list('counselor', flat=True).first()

                if recent_counselor:
                    counselor = User.objects.get(id=recent_counselor)
                    alert = CrisisAlert.objects.create(
                        student=request.user,
                        counselor=counselor,
                        wellness_check=check,
                        severity=_determine_severity(check),
                        trigger_reason=f'Low wellness scores: Mood={check.mood_score}, Anxiety={check.anxiety_level}, Stress={check.stress_level}',
                    )
                    Notification.objects.create(
                        recipient=counselor,
                        notification_type=Notification.NOTIF_CRISIS_ALERT,
                        title=f'⚠️ Crisis Alert: {request.user.full_name}',
                        body=f'{request.user.full_name} has submitted a wellness check with concerning scores. Please follow up.',
                        action_url=f'/progress/crisis/{alert.id}/',
                    )

            messages.success(request, f'Wellness check-in submitted! Your overall score is {check.overall_score}/10.')
            return redirect('wellness')

        except Exception as e:
            messages.error(request, 'Error submitting check-in. Please try again.')

    return render(request, 'progress/wellness_checkin.html', {
        'triggers_options': ['Exams', 'Family issues', 'Finances', 'Relationships', 'Work', 'Health', 'Loneliness'],
    })


def _determine_severity(check):
    if check.mood_score <= 2 or check.anxiety_level >= 9:
        return CrisisAlert.SEVERITY_CRITICAL
    elif check.mood_score <= 3 or check.anxiety_level >= 8:
        return CrisisAlert.SEVERITY_HIGH
    elif check.mood_score <= 4 or check.stress_level >= 8:
        return CrisisAlert.SEVERITY_MEDIUM
    return CrisisAlert.SEVERITY_LOW


# ── Goals ─────────────────────────────────────────────────────────────────────

@login_required
def goals_view(request):
    user = request.user
    if user.is_student:
        goals = ProgressGoal.objects.filter(student=user).order_by('-created_at')
    elif user.is_counselor:
        goals = ProgressGoal.objects.filter(
            student__institution=user.institution
        ).select_related('student').order_by('-created_at')
    else:
        goals = ProgressGoal.objects.none()

    status_filter = request.GET.get('status', '')
    if status_filter:
        goals = goals.filter(status=status_filter)

    return render(request, 'progress/goals.html', {
        'goals': goals[:50],
        'status_filter': status_filter,
        'statuses': ProgressGoal.STATUS_CHOICES,
        'categories': ProgressGoal.CATEGORY_CHOICES,
    })


@login_required
def create_goal_view(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id') if request.user.is_counselor else request.user.id
        student = get_object_or_404(User, id=student_id)

        from django.utils.dateparse import parse_date
        target_date_str = request.POST.get('target_date')
        target_date = parse_date(target_date_str) if target_date_str else None

        goal = ProgressGoal.objects.create(
            student=student,
            counselor=request.user if request.user.is_counselor else None,
            title=request.POST.get('title', '').strip(),
            description=request.POST.get('description', '').strip(),
            category=request.POST.get('category', 'other'),
            target_date=target_date,
        )

        Notification.objects.create(
            recipient=student,
            notification_type=Notification.NOTIF_GOAL,
            title='New Goal Created',
            body=f'A new goal "{goal.title}" has been created for you.',
            action_url='/goals/',
        )

        messages.success(request, f'Goal "{goal.title}" created successfully.')
        return redirect('goals')

    students = []
    if request.user.is_counselor:
        students = User.objects.filter(
            sessions_as_student__counselor=request.user,
            sessions_as_student__status='completed',
        ).distinct()

    return render(request, 'progress/create_goal.html', {
        'students': students,
        'categories': ProgressGoal.CATEGORY_CHOICES,
    })


@login_required
def goal_detail_view(request, goal_id):
    goal = get_object_or_404(ProgressGoal, id=goal_id)
    if goal.student != request.user and goal.counselor != request.user and not request.user.is_institution_admin:
        messages.error(request, 'Access denied.')
        return redirect('goals')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_progress':
            goal.progress_percentage = int(request.POST.get('progress_percentage', goal.progress_percentage))
            goal.student_reflection = request.POST.get('student_reflection', goal.student_reflection)
            if goal.progress_percentage == 100:
                goal.status = ProgressGoal.STATUS_COMPLETED
                goal.completed_at = timezone.now()
            goal.save()
            messages.success(request, 'Goal progress updated.')
        elif action == 'counselor_notes' and request.user.is_counselor:
            goal.counselor_notes = request.POST.get('counselor_notes', '')
            goal.save(update_fields=['counselor_notes'])
            messages.success(request, 'Notes saved.')
        return redirect('goal_detail', goal_id=goal_id)

    return render(request, 'progress/goal_detail.html', {'goal': goal})


# ── Analytics ─────────────────────────────────────────────────────────────────

@login_required
def analytics_view(request):
    if not (request.user.is_institution_admin or request.user.is_counselor or request.user.is_super_admin):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    institution = request.user.institution
    from apps.counseling.models import CounselingSession
    from datetime import timedelta

    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    sessions_qs = CounselingSession.objects.filter(counselor__institution=institution)
    wellness_qs = WellnessCheck.objects.filter(student__institution=institution)

    # Session stats
    total_sessions = sessions_qs.count()
    completed_sessions = sessions_qs.filter(status='completed').count()
    sessions_this_month = sessions_qs.filter(
        scheduled_at__date__gte=thirty_days_ago
    ).count()

    # Wellness stats
    avg_mood = wellness_qs.aggregate(avg=Avg('mood_score'))['avg'] or 0
    avg_wellness = wellness_qs.aggregate(avg=Avg('overall_score'))['avg'] or 0
    flagged_count = wellness_qs.filter(flagged_for_review=True, reviewed_by_counselor=False).count()

    # Trend data (last 30 days)
    from django.db.models.functions import TruncDate
    wellness_trend = list(
        wellness_qs.filter(date__gte=thirty_days_ago)
        .values('date')
        .annotate(avg_mood=Avg('mood_score'), avg_wellness=Avg('overall_score'), count=Count('id'))
        .order_by('date')
    )

    # Crisis alerts
    open_alerts = CrisisAlert.objects.filter(
        student__institution=institution, is_resolved=False
    ).count()

    ctx = {
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'sessions_this_month': sessions_this_month,
        'avg_mood': round(avg_mood, 1),
        'avg_wellness': round(avg_wellness, 1),
        'flagged_count': flagged_count,
        'open_alerts': open_alerts,
        'wellness_trend': wellness_trend,
        'student_count': User.objects.filter(institution=institution, role='student').count(),
        'counselor_count': User.objects.filter(institution=institution, role='counselor').count(),
    }
    return render(request, 'progress/analytics.html', ctx)


# ── Crisis alerts ─────────────────────────────────────────────────────────────

@login_required
def crisis_alerts_view(request):
    if not (request.user.is_counselor or request.user.is_institution_admin):
        return redirect('dashboard')

    if request.user.is_counselor:
        alerts = CrisisAlert.objects.filter(counselor=request.user)
    else:
        alerts = CrisisAlert.objects.filter(student__institution=request.user.institution)

    show_resolved = request.GET.get('resolved') == '1'
    if not show_resolved:
        alerts = alerts.filter(is_resolved=False)

    return render(request, 'progress/crisis_alerts.html', {
        'alerts': alerts.select_related('student', 'counselor').order_by('-created_at'),
        'show_resolved': show_resolved,
    })


@login_required
def resolve_crisis_view(request, alert_id):
    alert = get_object_or_404(CrisisAlert, id=alert_id, counselor=request.user)
    if request.method == 'POST':
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolution_notes = request.POST.get('resolution_notes', '')
        alert.save()
        messages.success(request, 'Crisis alert marked as resolved.')
    return redirect('crisis_alerts')
