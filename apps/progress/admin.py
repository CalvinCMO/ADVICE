from django.contrib import admin
from .models import WellnessCheck, ProgressGoal, ProgressReport, CrisisAlert

@admin.register(WellnessCheck)
class WellnessCheckAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'mood_score', 'overall_score', 'flagged_for_review']
    list_filter = ['flagged_for_review', 'reviewed_by_counselor']
    date_hierarchy = 'date'

@admin.register(ProgressGoal)
class ProgressGoalAdmin(admin.ModelAdmin):
    list_display = ['title', 'student', 'category', 'status', 'progress_percentage']
    list_filter = ['status', 'category']

@admin.register(ProgressReport)
class ProgressReportAdmin(admin.ModelAdmin):
    list_display = ['student', 'counselor', 'report_period_start', 'report_period_end', 'shared_with_student']

@admin.register(CrisisAlert)
class CrisisAlertAdmin(admin.ModelAdmin):
    list_display = ['student', 'counselor', 'severity', 'is_resolved', 'created_at']
    list_filter = ['severity', 'is_resolved']
