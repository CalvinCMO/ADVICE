from django.urls import path
from . import views

urlpatterns = [
    # Student
    path('student/dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('sessions/book/', views.book_session_view, name='book_session'),
    path('sessions/', views.my_sessions_view, name='my_sessions'),
    path('sessions/<uuid:session_id>/', views.session_detail_view, name='session_detail'),
    path('sessions/<uuid:session_id>/cancel/', views.cancel_session_view, name='cancel_session'),
    path('sessions/<uuid:session_id>/reschedule/', views.reschedule_session_view, name='reschedule_session'),
    path('sessions/<uuid:session_id>/feedback/', views.submit_feedback_view, name='submit_feedback'),

    # Counselor
    path('counselor/dashboard/', views.counselor_dashboard_view, name='counselor_dashboard'),
    path('sessions/<uuid:session_id>/start/', views.start_session_view, name='start_session'),
    path('sessions/<uuid:session_id>/complete/', views.complete_session_view, name='complete_session'),

    # Group
    path('group-sessions/', views.group_sessions_view, name='group_sessions'),
    path('group-sessions/<uuid:session_id>/join/', views.join_group_session_view, name='join_group_session'),
    path('group-sessions/create/', views.create_group_session_view, name='create_group_session'),

    # Counselors list
    path('counselors/', views.counselors_list_view, name='counselors_list'),
]
