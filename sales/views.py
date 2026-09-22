from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import Sale, SaleItem, BillMessage, build_bill_text, normalize_lk_mobile
from customers.models import Customer
from inventory.models import SparePart


class SaleList(LoginRequiredMixin, ListView):
    model = Sale
    template_name = 'sales/list.html'
    context_object_name = 'sales'
    ordering = ['-date']


@login_required
def sale_create(request):
    from maintenance.models import ServiceType
    from inventory.models import Category
    customers = Customer.objects.all()
    parts = SparePart.objects.select_related('category').order_by('category__name', 'name')
    services = ServiceType.objects.prefetch_related('parts').order_by('name')
    categories = Category.objects.order_by('name')
    ticked = [int(x) for x in request.GET.getlist('tick') if str(x).isdigit()]

    if request.method == 'POST':
        cid = request.POST.get('customer')
        customer = Customer.objects.filter(id=cid).first()
        if customer is None:
            messages.error(request, 'Please select a valid customer.')
            return render(request, 'sales/form.html', {'customers': customers, 'parts': parts, 'services': services, 'categories': categories, 'ticked': ticked})

        try:
            with transaction.atomic():
                part_ids = [p.id for p in parts]
                locked_parts = {
                    p.id: p for p in SparePart.objects.select_for_update().filter(id__in=part_ids)
                }

                items_to_create = []
                total = Decimal('0')
                for part_id, part in locked_parts.items():
                    if not request.POST.get(f'tick_{part_id}'):
                        continue
                    qty = int(request.POST.get(f'qty_{part_id}', 1) or 1)
                    if qty <= 0:
                        continue
                    if part.stock_qty < qty:
                        raise ValueError(f'Not enough stock for {part.name} (have {part.stock_qty}, need {qty}).')
                    raw_price = request.POST.get(f'price_{part_id}', '')
                    try:
                        unit_price = Decimal(raw_price) if raw_price else part.price
                    except Exception:
                        unit_price = part.price
                    if unit_price <= 0:
                        raise ValueError(f'Invalid price for {part.name}.')
                    if unit_price != part.price and not part.negotiable:
                        raise ValueError(f'{part.name} is fixed-price (Rs. {part.price}).')
                    items_to_create.append((part, qty, unit_price))
                    total += unit_price * qty

                if not items_to_create:
                    raise ValueError('Tick at least one part and set quantity greater than zero.')

                service = ServiceType.objects.filter(id=request.POST.get('service') or 0).first()
                labour = Decimal(request.POST.get('labour') or (service.labour_charge if service else 0) or 0)
                if labour < 0:
                    raise ValueError('Invalid labour charge.')
                if service and service.negotiable is False and labour != service.labour_charge:
                    raise ValueError(f'{service.name} labour is fixed at Rs. {service.labour_charge}.')
                total += labour

                sale = Sale.objects.create(
                    customer=customer, total=total, labour_charge=labour,
                    service_note=service.name if service else request.POST.get('service_note', ''),
                )
                for part, qty, unit_price in items_to_create:
                    SaleItem.objects.create(sale=sale, part=part, qty=qty, unit_price=unit_price)
                    part.stock_qty -= qty
                    part.save(update_fields=['stock_qty'])
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, 'sales/form.html', {'customers': customers, 'parts': parts, 'services': services, 'categories': categories, 'ticked': ticked})

        messages.success(request, f'Sale #{sale.id} saved — Rs. {sale.total}.')
        return redirect('sale-bill', sale_id=sale.id)

    return render(request, 'sales/form.html', {'customers': customers, 'parts': parts, 'services': services, 'categories': categories, 'ticked': ticked})


@login_required
def sale_bill(request, sale_id):
    import urllib.parse
    from django.conf import settings
    sale = Sale.objects.select_related('customer').prefetch_related('items__part', 'bill_messages').filter(id=sale_id).first()
    if sale is None:
        messages.error(request, 'Bill not found.')
        return redirect('sale-list')
    body = build_bill_text(sale)
    wa_number = normalize_lk_mobile(sale.customer.phone)
    wa_link = f"https://wa.me/{wa_number}?text={urllib.parse.quote(body)}"
    sms_configured = bool(getattr(settings, 'SMS_GATEWAY_URL', '') and getattr(settings, 'SMS_API_KEY', ''))
    return render(request, 'sales/bill.html', {
        'sale': sale, 'bill_text': body, 'wa_link': wa_link,
        'sms_configured': sms_configured,
    })


@login_required
def sale_send(request, sale_id):
    """Log the send-to-mobile action. WhatsApp opens on the shop PC/phone;
    SMS is queued until a gateway is configured in .env (see settings)."""
    import urllib.parse
    from django.conf import settings
    sale = Sale.objects.select_related('customer').filter(id=sale_id).first()
    if sale is None:
        messages.error(request, 'Bill not found.')
        return redirect('sale-list')
    if request.method != 'POST':
        return redirect('sale-bill', sale_id=sale.id)
    channel = request.POST.get('channel', 'whatsapp')
    body = build_bill_text(sale)
    phone = sale.customer.phone
    if channel == 'sms' and getattr(settings, 'SMS_GATEWAY_URL', '') and getattr(settings, 'SMS_API_KEY', ''):
        status = 'sent'  # gateway configured → extend here with requests.post to provider
    elif channel == 'sms':
        status = 'queued (no SMS gateway configured — set SMS_GATEWAY_URL/SMS_API_KEY in .env)'
    else:
        status = 'opened WhatsApp'
        channel = 'whatsapp'
    BillMessage.objects.create(sale=sale, phone=phone, channel=channel, body=body, status=status)
    if channel == 'whatsapp':
        wa_number = normalize_lk_mobile(phone)
        wa_link = f"https://wa.me/{wa_number}?text={urllib.parse.quote(body)}"
        messages.success(request, f'Bill #{sale.id} logged to {phone}. Opening WhatsApp…')
        from django.shortcuts import redirect as dj_redirect
        resp = dj_redirect(wa_link)
        return resp
    messages.success(request, f'Bill #{sale.id} recorded for {phone} ({status}).')
    return redirect('sale-bill', sale_id=sale.id)
