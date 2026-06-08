from django.contrib import admin
from .models import CounselingSession, GroupSession, SessionFeedback, CounselorAvailability

@admin.register(CounselingSession)
class CounselingSessionAdmin(admin.ModelAdmin):
    list_display = ['student', 'counselor', 'status', 'session_type', 'mode', 'scheduled_at']
    list_filter = ['status', 'session_type', 'mode']
    search_fields = ['student__email', 'counselor__email']
    date_hierarchy = 'scheduled_at'

@admin.register(GroupSession)
class GroupSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'facilitator', 'scheduled_at', 'max_participants', 'is_open']

@admin.register(SessionFeedback)
class SessionFeedbackAdmin(admin.ModelAdmin):
    list_display = ['session', 'rating', 'was_helpful', 'submitted_at']

@admin.register(CounselorAvailability)
class CounselorAvailabilityAdmin(admin.ModelAdmin):
    list_display = ['counselor', 'day_of_week', 'start_time', 'end_time', 'is_active']
