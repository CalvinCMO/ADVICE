"""
apps/accounts/models.py
Custom User model with RBAC for ADVICE platform.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', User.SUPER_ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('email_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Unified user model for all roles:
    Super Admin, Institution Admin, Counselor, Student.
    """

    SUPER_ADMIN = 'super_admin'
    INSTITUTION_ADMIN = 'institution_admin'
    COUNSELOR = 'counselor'
    STUDENT = 'student'

    ROLE_CHOICES = [
        (SUPER_ADMIN, 'Super Admin'),
        (INSTITUTION_ADMIN, 'Institution Admin'),
        (COUNSELOR, 'Counselor'),
        (STUDENT, 'Student'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=STUDENT)

    # Profile
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)

    GENDER_CHOICES = [
        ('M', 'Male'), ('F', 'Female'),
        ('NB', 'Non-binary'), ('P', 'Prefer not to say'),
    ]
    gender = models.CharField(max_length=5, choices=GENDER_CHOICES, blank=True)

    # Institution link
    institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='members',
    )

    # Student-specific
    student_id = models.CharField(max_length=50, blank=True)
    course = models.CharField(max_length=200, blank=True)
    year_of_study = models.PositiveSmallIntegerField(null=True, blank=True)

    # Counselor-specific
    license_number = models.CharField(max_length=100, blank=True)
    specializations = models.JSONField(default=list, blank=True)
    years_experience = models.PositiveSmallIntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    max_students = models.PositiveSmallIntegerField(default=30)
    available_hours = models.JSONField(default=dict, blank=True)

    # Security & status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    password_reset_token = models.UUIDField(null=True, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(null=True, blank=True)

    # Login protection
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # Notification prefs
    notify_session_reminders = models.BooleanField(default=True)
    notify_messages = models.BooleanField(default=True)
    notify_progress_updates = models.BooleanField(default=True)
    notify_email = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_super_admin(self):
        return self.role == self.SUPER_ADMIN

    @property
    def is_institution_admin(self):
        return self.role == self.INSTITUTION_ADMIN

    @property
    def is_counselor(self):
        return self.role == self.COUNSELOR

    @property
    def is_student(self):
        return self.role == self.STUDENT

    @property
    def is_locked(self):
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False

    def update_last_activity(self):
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])

    def record_failed_login(self):
        from django.conf import settings
        max_attempts = getattr(settings, 'LOGIN_MAX_ATTEMPTS', 5)
        lockout_mins = getattr(settings, 'LOGIN_LOCKOUT_DURATION_MINUTES', 60)
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=lockout_mins)
        self.save(update_fields=['failed_login_attempts', 'locked_until'])

    def reset_failed_logins(self):
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'locked_until'])

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        initials = f"{self.first_name[0]}{self.last_name[0]}".upper() if self.first_name else "?"
        return None


class InvitationCode(models.Model):
    """Invitation codes to control who joins an institution."""
    code = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    role = models.CharField(max_length=30, choices=User.ROLE_CHOICES, default=User.STUDENT)
    institution = models.ForeignKey(
        'institutions.Institution', on_delete=models.CASCADE, related_name='invitations'
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invitations_sent')
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='invitation_used')
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Invitation Code'

    def __str__(self):
        return f"Invite({self.code}) → {self.email}"

    @property
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at
