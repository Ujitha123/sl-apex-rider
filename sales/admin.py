from django.contrib import admin
from .models import Sale, SaleItem, BillMessage

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
    list_display = ('sale', 'phone', 'channel', 'status', 'created_at')
    list_filter = ('channel', 'status')
