from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import (
    Sale, SaleItem, BillMessage, Estimate, EstimateItem,
    build_bill_text, build_estimate_text, build_completion_text, normalize_lk_mobile,
)
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


class EstimateList(LoginRequiredMixin, ListView):
    model = Estimate
    template_name = 'sales/estimate_list.html'
    context_object_name = 'estimates'
    ordering = ['-created_at']


@login_required
def estimate_create(request):
    """Prepare a pre-service bill BEFORE work starts (no stock change)."""
    from maintenance.models import ServiceType
    from inventory.models import Category
    from motorcycles.models import Motorcycle
    customers = Customer.objects.all()
    bikes = Motorcycle.objects.select_related('customer').all()
    parts = SparePart.objects.select_related('category').order_by('category__name', 'name')
    services = ServiceType.objects.prefetch_related('parts').order_by('name')
    categories = Category.objects.order_by('name')

    if request.method == 'POST':
        customer = Customer.objects.filter(id=request.POST.get('customer')).first()
        if customer is None:
            messages.error(request, 'Please select a valid customer.')
            return render(request, 'sales/estimate_form.html', {'customers': customers, 'bikes': bikes, 'parts': parts, 'services': services, 'categories': categories})
        bike = Motorcycle.objects.filter(id=request.POST.get('motorcycle') or 0).first()
        service = ServiceType.objects.filter(id=request.POST.get('service') or 0).first()
        try:
            labour = Decimal(request.POST.get('labour') or (service.labour_charge if service else 0) or 0)
        except Exception:
            labour = Decimal('0')
        items, total = [], labour
        for part in parts:
            if not request.POST.get(f'tick_{part.id}'):
                continue
            try:
                qty = int(request.POST.get(f'qty_{part.id}', 1) or 1)
            except ValueError:
                qty = 1
            if qty <= 0:
                continue
            raw = request.POST.get(f'price_{part.id}', '')
            try:
                price = Decimal(raw) if raw else part.price
            except Exception:
                price = part.price
            if price != part.price and not part.negotiable:
                messages.error(request, f'{part.name} is fixed-price (Rs. {part.price}).')
                return render(request, 'sales/estimate_form.html', {'customers': customers, 'bikes': bikes, 'parts': parts, 'services': services, 'categories': categories})
            items.append((part, qty, price))
            total += price * qty
        if not items and labour <= 0:
            messages.error(request, 'Tick at least one part or enter a labour charge.')
            return render(request, 'sales/estimate_form.html', {'customers': customers, 'bikes': bikes, 'parts': parts, 'services': services, 'categories': categories})
        est = Estimate.objects.create(
            customer=customer, motorcycle=bike,
            service_note=service.name if service else request.POST.get('service_note', ''),
            labour_charge=labour, total=total,
        )
        for part, qty, price in items:
            EstimateItem.objects.create(estimate=est, part=part, qty=qty, unit_price=price)
        messages.success(request, f'Estimate #{est.id} prepared — Rs. {est.total}. Send it to the phone.')
        return redirect('estimate-detail', est_id=est.id)
    return render(request, 'sales/estimate_form.html', {'customers': customers, 'bikes': bikes, 'parts': parts, 'services': services, 'categories': categories})


@login_required
def estimate_detail(request, est_id):
    import urllib.parse
    est = Estimate.objects.select_related('customer', 'motorcycle').prefetch_related('items__part', 'messages').filter(id=est_id).first()
    if est is None:
        messages.error(request, 'Estimate not found.')
        return redirect('estimate-list')
    body = build_estimate_text(est)
    wa_link = f"https://wa.me/{normalize_lk_mobile(est.customer.phone)}?text={urllib.parse.quote(body)}"
    return render(request, 'sales/estimate_detail.html', {'est': est, 'bill_text': body, 'wa_link': wa_link})


def _log_send(estimate_or_sale, channel, body, phone, kind):
    from django.conf import settings
    if channel == 'sms' and getattr(settings, 'SMS_GATEWAY_URL', '') and getattr(settings, 'SMS_API_KEY', ''):
        status = 'sent'
    elif channel == 'sms':
        status = 'queued (no SMS gateway configured — set SMS_GATEWAY_URL/SMS_API_KEY in .env)'
    else:
        status = 'opened WhatsApp'
        channel = 'whatsapp'
    kw = {'phone': phone, 'channel': channel, 'body': body, 'status': status, 'kind': kind}
    if isinstance(estimate_or_sale, Estimate):
        kw['estimate'] = estimate_or_sale
    else:
        kw['sale'] = estimate_or_sale
    return BillMessage.objects.create(**kw), status


@login_required
def estimate_send(request, est_id):
    """Send the PRE-service estimate SMS/WhatsApp to the phone."""
    import urllib.parse
    est = Estimate.objects.select_related('customer').filter(id=est_id).first()
    if est is None:
        messages.error(request, 'Estimate not found.')
        return redirect('estimate-list')
    if request.method != 'POST':
        return redirect('estimate-detail', est_id=est.id)
    channel = request.POST.get('channel', 'sms')
    body = build_estimate_text(est)
    msg, status = _log_send(est, channel, body, est.customer.phone, 'estimate')
    if est.status == 'draft':
        est.status = 'sent'
        est.save(update_fields=['status'])
    if msg.channel == 'whatsapp':
        wa_link = f"https://wa.me/{normalize_lk_mobile(est.customer.phone)}?text={urllib.parse.quote(body)}"
        messages.success(request, f'Estimate #{est.id} logged to {est.customer.phone}. Opening WhatsApp…')
        from django.shortcuts import redirect as dj_redirect
        return dj_redirect(wa_link)
    messages.success(request, f'Estimate #{est.id} sent/queued to {est.customer.phone} ({status}).')
    return redirect('estimate-detail', est_id=est.id)


@login_required
def estimate_convert(request, est_id):
    """After approval: convert estimate → real Sale (stock decrements here, not before)."""
    est = Estimate.objects.prefetch_related('items__part').filter(id=est_id).first()
    if est is None:
        messages.error(request, 'Estimate not found.')
        return redirect('estimate-list')
    if est.sale_id:
        messages.error(request, f'Estimate #{est.id} is already Sale #{est.sale_id}.')
        return redirect('sale-bill', sale_id=est.sale_id)
    if request.method != 'POST':
        return redirect('estimate-detail', est_id=est.id)
    try:
        with transaction.atomic():
            locked = {p.id: p for p in SparePart.objects.select_for_update().filter(id__in=[i.part_id for i in est.items.all()])}
            total = est.labour_charge
            for item in est.items.all():
                part = locked[item.part_id]
                if part.stock_qty < item.qty:
                    raise ValueError(f'Not enough stock for {part.name} (have {part.stock_qty}, need {item.qty}).')
                total += item.unit_price * item.qty
            sale = Sale.objects.create(customer=est.customer, total=total, labour_charge=est.labour_charge, service_note=est.service_note)
            for item in est.items.all():
                part = locked[item.part_id]
                SaleItem.objects.create(sale=sale, part=part, qty=item.qty, unit_price=item.unit_price)
                part.stock_qty -= item.qty
                part.save(update_fields=['stock_qty'])
            est.sale = sale
            est.status = 'approved'
            est.save(update_fields=['sale', 'status'])
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('estimate-detail', est_id=est.id)
    messages.success(request, f'Estimate #{est.id} → Sale #{sale.id} (Rs. {sale.total}).')
    return redirect('sale-bill', sale_id=sale.id)


@login_required
def estimate_complete(request, est_id):
    """AFTER service is done: send completion ALERT sms to the phone."""
    import urllib.parse
    est = Estimate.objects.select_related('customer', 'motorcycle').filter(id=est_id).first()
    if est is None:
        messages.error(request, 'Estimate not found.')
        return redirect('estimate-list')
    if request.method != 'POST':
        return redirect('estimate-detail', est_id=est.id)
    channel = request.POST.get('channel', 'sms')
    body = build_completion_text(est)
    msg, status = _log_send(est, channel, body, est.customer.phone, 'completion_alert')
    est.status = 'completed'
    est.save(update_fields=['status'])
    if msg.channel == 'whatsapp':
        wa_link = f"https://wa.me/{normalize_lk_mobile(est.customer.phone)}?text={urllib.parse.quote(body)}"
        messages.success(request, 'Service completion alert logged. Opening WhatsApp…')
        from django.shortcuts import redirect as dj_redirect
        return dj_redirect(wa_link)
    messages.success(request, f'Completion alert sent/queued to {est.customer.phone} ({status}).')
    return redirect('estimate-detail', est_id=est.id)
