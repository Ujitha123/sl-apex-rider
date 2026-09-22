from django.contrib import admin
from .models import Sale, SaleItem, BillMessage, Estimate, EstimateItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1

class BillMessageInline(admin.TabularInline):
    model = BillMessage
    extra = 0
    readonly_fields = ('phone', 'channel', 'status', 'created_at')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'date', 'total')
    inlines = [SaleItemInline, BillMessageInline]

@admin.register(BillMessage)
class BillMessageAdmin(admin.ModelAdmin):
    list_display = ('sale', 'estimate', 'kind', 'phone', 'channel', 'status', 'created_at')
    list_filter = ('kind', 'channel', 'status')

class EstimateItemInline(admin.TabularInline):
    model = EstimateItem
    extra = 0

@admin.register(Estimate)
class EstimateAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'motorcycle', 'status', 'total', 'created_at')
    list_filter = ('status',)
    inlines = [EstimateItemInline]
