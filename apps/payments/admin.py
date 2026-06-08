from django.contrib import admin
from .models import SubscriptionPlan, InstitutionSubscription, PaymentRecord

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'billing_cycle', 'price_usd', 'max_students', 'is_active']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(InstitutionSubscription)
class InstitutionSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['institution', 'plan', 'status', 'started_at']
    list_filter = ['status']

@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ['institution', 'amount_usd', 'gateway', 'status', 'created_at']
    list_filter = ['status', 'gateway']
