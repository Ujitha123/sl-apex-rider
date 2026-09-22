from django.contrib import admin
from .models import Category, SparePart

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = ('name', 'part_number', 'price', 'stock_qty', 'min_stock')
    search_fields = ('name', 'part_number', 'compatible_models')
    list_filter = ('category',)
