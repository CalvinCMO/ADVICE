from django.urls import path
from . import views

urlpatterns = [
    path('billing/', views.billing_view, name='billing'),
    path('plans/', views.plans_view, name='plans'),
]
