from django.contrib import admin
from .models import Motorcycle

@admin.register(Motorcycle)
class MotorcycleAdmin(admin.ModelAdmin):
    list_display = ('plate_no', 'brand', 'model', 'customer', 'mileage')
    search_fields = ('plate_no', 'model')
