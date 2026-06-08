from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('password-reset/', views.password_reset_request_view, name='password_reset'),
    path('password-reset/<uuid:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('notifications/preferences/', views.notification_preferences_view, name='notification_prefs'),

    # Admin
    path('admin-panel/', views.admin_dashboard_view, name='admin_dashboard'),
    path('institution/dashboard/', views.institution_dashboard_view, name='institution_dashboard'),
    path('institution/users/', views.manage_users_view, name='manage_users'),
    path('institution/users/<uuid:user_id>/toggle/', views.toggle_user_status_view, name='toggle_user_status'),
    path('institution/invitations/', views.manage_invitations_view, name='manage_invitations'),
    path('institution/invitations/create/', views.create_invitation_view, name='create_invitation'),
]
