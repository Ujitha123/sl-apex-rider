from django.shortcuts import render
from customers.models import Customer
from motorcycles.models import Motorcycle
from inventory.models import SparePart
from sales.models import Sale
from maintenance.models import PredictiveAlert
from django.db.models import Sum

def home(request):
    import json
    stock_ok = SparePart.objects.filter(stock_qty__gt=5).count()
    stock_low = SparePart.objects.filter(stock_qty__lte=5).count()
    recent = list(Sale.objects.order_by('-date')[:5])
    ctx = {
        'customers': Customer.objects.count(),
        'bikes': Motorcycle.objects.count(),
        'parts': SparePart.objects.count(),
        'sales_total': Sale.objects.aggregate(s=Sum('total'))['s'] or 0,
        'low_stock': SparePart.objects.filter(stock_qty__lte=5)[:10],
        'alerts': PredictiveAlert.objects.filter(is_done=False)[:10],
        'recent_sales': recent,
        'stock_ok': stock_ok,
        'stock_low': stock_low,
        'sales_labels_json': json.dumps([s.customer.name for s in recent]),
        'sales_values_json': json.dumps([float(s.total) for s in recent]),
    }
    return render(request, 'dashboard/home.html', ctx)
