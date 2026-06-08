"""
apps/counseling/views.py
Session management views for students and counselors.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Avg
from datetime import timedelta

from .models import CounselingSession, GroupSession, GroupSessionParticipant, SessionFeedback, CounselorAvailability
from apps.accounts.models import User
from apps.messaging.models import Notification


def _notify(recipient, notif_type, title, body, action_url=''):
    Notification.objects.create(
        recipient=recipient,
        notification_type=notif_type,
        title=title,
        body=body,
        action_url=action_url,
    )


# ── Student views ────────────────────────────────────────────────────────────

@login_required
def student_dashboard_view(request):
    user = request.user
    if not user.is_student:
        return redirect('dashboard')

    now = timezone.now()
    upcoming = CounselingSession.objects.filter(
        student=user,
        status__in=['scheduled', 'in_progress'],
        scheduled_at__gte=now,
    ).select_related('counselor').order_by('scheduled_at')[:5]

    past = CounselingSession.objects.filter(
        student=user,
        status='completed',
    ).order_by('-scheduled_at')[:3]

    from apps.progress.models import WellnessCheck, ProgressGoal
    recent_check = WellnessCheck.objects.filter(student=user).first()
    active_goals = ProgressGoal.objects.filter(student=user, status='active').count()

    # Counselor list in institution
    counselors = User.objects.filter(
        institution=user.institution,
        role=User.COUNSELOR,
        is_verified=True,
        is_active=True,
    )

    group_sessions = GroupSession.objects.filter(
        facilitator__institution=user.institution,
        scheduled_at__gte=now,
        is_open=True,
    ).order_by('scheduled_at')[:3]

    ctx = {
        'upcoming_sessions': upcoming,
        'past_sessions': past,
        'recent_wellness': recent_check,
        'active_goals': active_goals,
        'counselors': counselors,
        'group_sessions': group_sessions,
    }
    return render(request, 'dashboard/student.html', ctx)


@login_required
def book_session_view(request):
    if not request.user.is_student:
        return redirect('dashboard')

    counselors = User.objects.filter(
        institution=request.user.institution,
        role=User.COUNSELOR,
        is_verified=True,
        is_active=True,
    )

    if request.method == 'POST':
        counselor_id = request.POST.get('counselor_id')
        scheduled_at = request.POST.get('scheduled_at')
        duration = int(request.POST.get('duration', 60))
        session_type = request.POST.get('session_type', 'individual')
        mode = request.POST.get('mode', 'online')
        reason = request.POST.get('reason', '').strip()
        mood_before = request.POST.get('mood_before')

        if not reason:
            messages.error(request, 'Please provide a reason for the session.')
            return render(request, 'counseling/book_session.html', {'counselors': counselors})

        try:
            counselor = User.objects.get(id=counselor_id, role=User.COUNSELOR)
            from django.utils.dateparse import parse_datetime
            scheduled_dt = parse_datetime(scheduled_at)
            if not scheduled_dt:
                raise ValueError("Invalid date")
            if scheduled_dt <= timezone.now():
                messages.error(request, 'Session must be scheduled in the future.')
                return render(request, 'counseling/book_session.html', {'counselors': counselors})
        except (User.DoesNotExist, ValueError):
            messages.error(request, 'Invalid counselor or date.')
            return render(request, 'counseling/book_session.html', {'counselors': counselors})

        session = CounselingSession.objects.create(
            student=request.user,
            counselor=counselor,
            scheduled_at=scheduled_dt,
            duration_minutes=duration,
            session_type=session_type,
            mode=mode,
            reason=reason,
            student_mood_before=mood_before if mood_before else None,
        )

        _notify(counselor, 'session_reminder',
                f'New session booked by {request.user.full_name}',
                f'{request.user.full_name} has booked a session on {scheduled_dt.strftime("%b %d at %H:%M")}.',
                f'/sessions/{session.id}/')

        messages.success(request, f'Session booked with {counselor.full_name} on {scheduled_dt.strftime("%B %d, %Y at %H:%M")}.')
        return redirect('my_sessions')

    return render(request, 'counseling/book_session.html', {'counselors': counselors})


@login_required
def my_sessions_view(request):
    user = request.user
    now = timezone.now()
    tab = request.GET.get('tab', 'upcoming')

    if user.is_student:
        base_qs = CounselingSession.objects.filter(student=user)
    elif user.is_counselor:
        base_qs = CounselingSession.objects.filter(counselor=user)
    else:
        base_qs = CounselingSession.objects.none()

    if tab == 'upcoming':
        sessions = base_qs.filter(status__in=['scheduled', 'in_progress'], scheduled_at__gte=now).order_by('scheduled_at')
    elif tab == 'past':
        sessions = base_qs.filter(status='completed').order_by('-scheduled_at')
    elif tab == 'cancelled':
        sessions = base_qs.filter(status__in=['cancelled', 'no_show']).order_by('-scheduled_at')
    else:
        sessions = base_qs.order_by('-scheduled_at')

    return render(request, 'counseling/my_sessions.html', {
        'sessions': sessions.select_related('student', 'counselor')[:30],
        'tab': tab,
    })


@login_required
def session_detail_view(request, session_id):
    user = request.user
    session = get_object_or_404(
        CounselingSession,
        id=session_id,
    )
    if session.student != user and session.counselor != user and not user.is_institution_admin:
        messages.error(request, 'Access denied.')
        return redirect('my_sessions')

    feedback = None
    try:
        feedback = session.feedback
    except SessionFeedback.DoesNotExist:
        pass

    return render(request, 'counseling/session_detail.html', {
        'session': session,
        'feedback': feedback,
        'can_start': user.is_counselor and session.status == 'scheduled',
        'can_complete': user.is_counselor and session.status == 'in_progress',
        'can_cancel': session.status in ['scheduled'] and (user == session.student or user == session.counselor),
        'can_feedback': user.is_student and session.status == 'completed' and not feedback,
    })


@login_required
def cancel_session_view(request, session_id):
    session = get_object_or_404(CounselingSession, id=session_id)
    if session.student != request.user and session.counselor != request.user:
        messages.error(request, 'Access denied.')
        return redirect('my_sessions')

    if session.status != 'scheduled':
        messages.error(request, 'Only scheduled sessions can be cancelled.')
        return redirect('session_detail', session_id=session_id)

    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        session.status = CounselingSession.STATUS_CANCELLED
        session.cancelled_by = request.user
        session.cancellation_reason = reason
        session.save()

        other = session.counselor if request.user == session.student else session.student
        _notify(other, 'session_cancelled',
                'Session Cancelled',
                f'Your session on {session.scheduled_at.strftime("%b %d")} has been cancelled. Reason: {reason}',
                '/sessions/')

        messages.success(request, 'Session cancelled.')
        return redirect('my_sessions')

    return render(request, 'counseling/cancel_session.html', {'session': session})


@login_required
def reschedule_session_view(request, session_id):
    session = get_object_or_404(CounselingSession, id=session_id)
    if session.student != request.user and session.counselor != request.user:
        return redirect('my_sessions')

    if request.method == 'POST':
        from django.utils.dateparse import parse_datetime
        new_dt_str = request.POST.get('new_datetime')
        new_dt = parse_datetime(new_dt_str)
        if new_dt and new_dt > timezone.now():
            old_dt = session.scheduled_at
            session.scheduled_at = new_dt
            session.status = CounselingSession.STATUS_RESCHEDULED
            session.save()

            other = session.counselor if request.user == session.student else session.student
            _notify(other, 'session_rescheduled',
                    'Session Rescheduled',
                    f'Your session has been rescheduled from {old_dt.strftime("%b %d %H:%M")} to {new_dt.strftime("%b %d %H:%M")}.',
                    f'/sessions/{session.id}/')

            messages.success(request, 'Session rescheduled.')
            return redirect('session_detail', session_id=session_id)
        else:
            messages.error(request, 'Please choose a future date and time.')

    return render(request, 'counseling/reschedule_session.html', {'session': session})


# ── Counselor views ──────────────────────────────────────────────────────────

@login_required
def counselor_dashboard_view(request):
    if not request.user.is_counselor:
        return redirect('dashboard')

    user = request.user
    now = timezone.now()

    upcoming = CounselingSession.objects.filter(
        counselor=user,
        status__in=['scheduled', 'in_progress'],
        scheduled_at__gte=now,
    ).select_related('student').order_by('scheduled_at')[:10]

    today_sessions = CounselingSession.objects.filter(
        counselor=user,
        scheduled_at__date=now.date(),
        status__in=['scheduled', 'in_progress'],
    ).count()

    from apps.progress.models import CrisisAlert, WellnessCheck
    active_alerts = CrisisAlert.objects.filter(
        counselor=user, is_resolved=False
    ).select_related('student').order_by('-created_at')[:5]

    flagged_wellness = WellnessCheck.objects.filter(
        student__institution=user.institution,
        flagged_for_review=True,
        reviewed_by_counselor=False,
    ).select_related('student').order_by('-checked_at')[:5]

    my_students = User.objects.filter(
        sessions_as_student__counselor=user,
        sessions_as_student__status='completed',
    ).distinct()

    ctx = {
        'upcoming_sessions': upcoming,
        'today_sessions_count': today_sessions,
        'active_alerts': active_alerts,
        'flagged_wellness': flagged_wellness,
        'student_count': my_students.count(),
    }
    return render(request, 'dashboard/counselor.html', ctx)


@login_required
def start_session_view(request, session_id):
    if not request.user.is_counselor:
        return redirect('dashboard')
    session = get_object_or_404(CounselingSession, id=session_id, counselor=request.user)
    if session.status == 'scheduled':
        session.start()
        messages.success(request, 'Session started.')
    return redirect('session_detail', session_id=session_id)


@login_required
def complete_session_view(request, session_id):
    if not request.user.is_counselor:
        return redirect('dashboard')
    session = get_object_or_404(CounselingSession, id=session_id, counselor=request.user)

    if request.method == 'POST' and session.status == 'in_progress':
        session.counselor_notes = request.POST.get('counselor_notes', '')
        session.summary = request.POST.get('summary', '')
        session.follow_up_required = request.POST.get('follow_up_required') == 'on'
        session.follow_up_notes = request.POST.get('follow_up_notes', '')
        mood_after = request.POST.get('student_mood_after')
        if mood_after:
            session.student_mood_after = int(mood_after)
        session.complete()

        _notify(session.student, 'progress_update',
                'Session Completed',
                f'Your session with {request.user.full_name} has been completed. A summary is available.',
                f'/sessions/{session.id}/')

        messages.success(request, 'Session completed and notes saved.')
        return redirect('session_detail', session_id=session_id)

    return render(request, 'counseling/complete_session.html', {'session': session})


@login_required
def submit_feedback_view(request, session_id):
    if not request.user.is_student:
        return redirect('dashboard')
    session = get_object_or_404(CounselingSession, id=session_id, student=request.user, status='completed')

    if hasattr(session, 'feedback'):
        messages.info(request, 'Feedback already submitted.')
        return redirect('session_detail', session_id=session_id)

    if request.method == 'POST':
        SessionFeedback.objects.create(
            session=session,
            rating=int(request.POST.get('rating', 3)),
            was_helpful=request.POST.get('was_helpful') == 'yes',
            comments=request.POST.get('comments', ''),
            would_recommend=request.POST.get('would_recommend') == 'yes',
        )
        messages.success(request, 'Thank you for your feedback!')
        return redirect('session_detail', session_id=session_id)

    return render(request, 'counseling/submit_feedback.html', {'session': session})


# ── Group sessions ───────────────────────────────────────────────────────────

@login_required
def group_sessions_view(request):
    now = timezone.now()
    sessions = GroupSession.objects.filter(
        facilitator__institution=request.user.institution,
        scheduled_at__gte=now,
        is_open=True,
    ).prefetch_related('participants').order_by('scheduled_at')

    my_registrations = set(
        GroupSessionParticipant.objects.filter(user=request.user).values_list('group_session_id', flat=True)
    )

    return render(request, 'counseling/group_sessions.html', {
        'sessions': sessions,
        'my_registrations': my_registrations,
    })


@login_required
def join_group_session_view(request, session_id):
    gs = get_object_or_404(GroupSession, id=session_id)
    if gs.is_full:
        messages.error(request, 'This session is full.')
    else:
        GroupSessionParticipant.objects.get_or_create(group_session=gs, user=request.user)
        messages.success(request, f'You have joined "{gs.title}".')
    return redirect('group_sessions')


@login_required
def create_group_session_view(request):
    if not request.user.is_counselor:
        return redirect('dashboard')

    if request.method == 'POST':
        from django.utils.dateparse import parse_datetime
        GroupSession.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            facilitator=request.user,
            max_participants=int(request.POST.get('max_participants', 15)),
            scheduled_at=parse_datetime(request.POST.get('scheduled_at')),
            duration_minutes=int(request.POST.get('duration_minutes', 90)),
            topic=request.POST.get('topic', ''),
            is_anonymous=request.POST.get('is_anonymous') == 'on',
        )
        messages.success(request, 'Group session created.')
        return redirect('group_sessions')

    return render(request, 'counseling/create_group_session.html')


# ── Counselor list for students ──────────────────────────────────────────────

@login_required
def counselors_list_view(request):
    counselors = User.objects.filter(
        institution=request.user.institution,
        role=User.COUNSELOR,
        is_verified=True,
        is_active=True,
    ).order_by('first_name')
    return render(request, 'counseling/counselors.html', {'counselors': counselors})
