from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import Sale, SaleItem
from customers.models import Customer
from inventory.models import SparePart

class SaleList(ListView):
    model = Sale
    template_name = 'sales/list.html'
    context_object_name = 'sales'
    ordering = ['-date']

def sale_create(request):
    customers = Customer.objects.all()
    parts = SparePart.objects.all()
    if request.method == 'POST':
        cid = request.POST.get('customer')
        customer = Customer.objects.get(id=cid)
        sale = Sale.objects.create(customer=customer, total=0)
        total = 0
        for part in parts:
            qty = int(request.POST.get(f'qty_{part.id}', 0) or 0)
            if qty > 0 and part.stock_qty >= qty:
                SaleItem.objects.create(sale=sale, part=part, qty=qty, unit_price=part.price)
                part.stock_qty -= qty
                part.save()
                total += float(part.price) * qty
        sale.total = total
        sale.save()
        return redirect('sale-list')
    return render(request, 'sales/form.html', {'customers': customers, 'parts': parts})
