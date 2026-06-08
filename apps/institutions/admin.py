from django.contrib import admin
from .models import Institution

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'plan', 'status', 'country', 'created_at']
    list_filter = ['plan', 'status', 'country']
    search_fields = ['name', 'email']
    prepopulated_fields = {'slug': ('name',)}
