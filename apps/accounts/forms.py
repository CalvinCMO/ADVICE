"""
apps/accounts/forms.py
Django forms for authentication and user management.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.utils import timezone
from .models import User, InvitationCode


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
            'placeholder': 'your@email.com',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        })
    )
    remember_me = forms.BooleanField(required=False)


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition',
            'placeholder': 'Minimum 8 characters',
        })
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition',
            'placeholder': 'Repeat your password',
        })
    )
    invitation_code = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition',
            'placeholder': 'Invitation code (optional)',
        })
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'institution']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition',
                'placeholder': 'Last name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition',
                'placeholder': 'your@university.edu',
            }),
            'role': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition',
            }),
            'institution': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Students and counselors can self-register
        self.fields['role'].choices = [
            (User.STUDENT, 'Student'),
            (User.COUNSELOR, 'Counselor'),
        ]
        self.fields['institution'].required = False

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return p2

    def clean_password1(self):
        p = self.cleaned_data.get('password1')
        if p and len(p) < 8:
            raise forms.ValidationError("Password must be at least 8 characters.")
        return p

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'date_of_birth',
            'bio', 'gender', 'avatar',
            # Student fields
            'student_id', 'course', 'year_of_study',
            # Counselor fields
            'license_number', 'years_experience',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'gender': forms.Select(attrs={'class': 'form-input'}),
            'student_id': forms.TextInput(attrs={'class': 'form-input'}),
            'course': forms.TextInput(attrs={'class': 'form-input'}),
            'year_of_study': forms.NumberInput(attrs={'class': 'form-input'}),
            'license_number': forms.TextInput(attrs={'class': 'form-input'}),
            'years_experience': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your registered email',
        })
    )


class SetNewPasswordForm(forms.Form):
    password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'New password'})
    )
    password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm new password'})
    )

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return p2


class NotificationPreferencesForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['notify_session_reminders', 'notify_messages', 'notify_progress_updates', 'notify_email']
