from django.urls import path
from . import views

urlpatterns = [
    path('wellness/', views.wellness_view, name='wellness'),
    path('wellness/check-in/', views.wellness_checkin_view, name='wellness_checkin'),
    path('goals/', views.goals_view, name='goals'),
    path('goals/create/', views.create_goal_view, name='create_goal'),
    path('goals/<uuid:goal_id>/', views.goal_detail_view, name='goal_detail'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('progress/crisis/', views.crisis_alerts_view, name='crisis_alerts'),
    path('progress/crisis/<uuid:alert_id>/resolve/', views.resolve_crisis_view, name='resolve_crisis'),
]
