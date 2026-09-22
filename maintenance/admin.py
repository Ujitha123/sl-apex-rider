from django.contrib import admin
from .models import ServiceRecord, PredictiveAlert

@admin.register(ServiceRecord)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('motorcycle', 'mileage', 'service_date', 'next_due_mileage')

@admin.register(PredictiveAlert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('motorcycle', 'predicted_part', 'due_mileage', 'is_done')
    list_filter = ('is_done',)
