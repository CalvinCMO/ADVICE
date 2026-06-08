from django.urls import path
from . import views

urlpatterns = [
    path('messages/', views.conversations_view, name='conversations'),
    path('messages/new/', views.start_conversation_view, name='start_conversation'),
    path('messages/<uuid:conv_id>/', views.conversation_detail_view, name='conversation_detail'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<uuid:notif_id>/read/', views.mark_notification_read_view, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
]
