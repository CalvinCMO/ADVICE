from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, InvitationCode

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'role', 'institution', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'institution']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'phone', 'bio', 'gender', 'avatar')}),
        ('Role & Institution', {'fields': ('role', 'institution')}),
        ('Student', {'fields': ('student_id', 'course', 'year_of_study')}),
        ('Counselor', {'fields': ('license_number', 'specializations', 'years_experience', 'is_verified', 'max_students')}),
        ('Status', {'fields': ('is_active', 'is_staff', 'is_superuser', 'email_verified')}),
        ('Notifications', {'fields': ('notify_session_reminders', 'notify_messages', 'notify_progress_updates', 'notify_email')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2')}),
    )

@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'email', 'role', 'institution', 'is_used', 'expires_at']
    list_filter = ['role', 'is_used']
