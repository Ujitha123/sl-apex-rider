from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import Sale, SaleItem
from customers.models import Customer
from inventory.models import SparePart


class SaleList(LoginRequiredMixin, ListView):
    model = Sale
    template_name = 'sales/list.html'
    context_object_name = 'sales'
    ordering = ['-date']


@login_required
def sale_create(request):
    customers = Customer.objects.all()
    parts = SparePart.objects.all()

    if request.method == 'POST':
        cid = request.POST.get('customer')
        customer = Customer.objects.filter(id=cid).first()
        if customer is None:
            messages.error(request, 'Please select a valid customer.')
            return render(request, 'sales/form.html', {'customers': customers, 'parts': parts})

        try:
            with transaction.atomic():
                # Lock the part rows for this sale so two concurrent sales
                # can't both pass the stock check and oversell the same part.
                part_ids = [p.id for p in parts]
                locked_parts = {
                    p.id: p for p in SparePart.objects.select_for_update().filter(id__in=part_ids)
                }

                items_to_create = []
                total = Decimal('0')
                for part_id, part in locked_parts.items():
                    qty = int(request.POST.get(f'qty_{part_id}', 0) or 0)
                    if qty <= 0:
                        continue
                    if part.stock_qty < qty:
                        raise ValueError(f'Not enough stock for {part.name} (have {part.stock_qty}, need {qty}).')
                    items_to_create.append((part, qty))
                    total += part.price * qty

                if not items_to_create:
                    raise ValueError('Select at least one part with a quantity greater than zero.')

                sale = Sale.objects.create(customer=customer, total=total)
                for part, qty in items_to_create:
                    SaleItem.objects.create(sale=sale, part=part, qty=qty, unit_price=part.price)
                    part.stock_qty -= qty
                    part.save(update_fields=['stock_qty'])
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, 'sales/form.html', {'customers': customers, 'parts': parts})

        return redirect('sale-list')

    return render(request, 'sales/form.html', {'customers': customers, 'parts': parts})
