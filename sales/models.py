from django.db import models
from customers.models import Customer
from inventory.models import SparePart


class Sale(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sales')
    date = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    service_note = models.CharField(max_length=200, blank=True)
    labour_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Sale #{self.id} - {self.customer.name}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    part = models.ForeignKey(SparePart, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.part.price
        super().save(*args, **kwargs)


class BillMessage(models.Model):
    """Record of a bill/estimate/alert sent (or queued) to the customer's mobile."""
    KIND_CHOICES = [
        ('estimate', 'Pre-service estimate'),
        ('final_bill', 'Final bill'),
        ('completion_alert', 'Service completion alert'),
    ]
    CHANNEL_CHOICES = [('whatsapp', 'WhatsApp'), ('sms', 'SMS')]
    sale = models.ForeignKey(Sale, null=True, blank=True, on_delete=models.CASCADE, related_name='bill_messages')
    estimate = models.ForeignKey('Estimate', null=True, blank=True, on_delete=models.CASCADE, related_name='messages')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='final_bill')
    phone = models.CharField(max_length=20)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='whatsapp')
    body = models.TextField()
    status = models.CharField(max_length=60, default='logged')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target = f"estimate #{self.estimate_id}" if self.estimate_id else f"bill #{self.sale_id}"
        return f"{target} → {self.phone} via {self.channel} ({self.status})"


class Estimate(models.Model):
    """Pre-service bill prepared BEFORE work starts. Sent to phone, then
    converted to a Sale (stock decrements) after approval/completion."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent to customer'),
        ('approved', 'Approved'),
        ('completed', 'Service done'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='estimates')
    motorcycle = models.ForeignKey('motorcycles.Motorcycle', null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='estimates')
    service_note = models.CharField(max_length=200, blank=True)
    labour_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    sale = models.OneToOneField(Sale, null=True, blank=True, on_delete=models.SET_NULL, related_name='estimate')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Estimate #{self.id} - {self.customer.name} ({self.status})"


class EstimateItem(models.Model):
    estimate = models.ForeignKey(Estimate, on_delete=models.CASCADE, related_name='items')
    part = models.ForeignKey(SparePart, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)


def normalize_lk_mobile(phone: str) -> str:
    """07XXXXXXXX → 947XXXXXXXX for wa.me links. Leaves other formats untouched."""
    digits = ''.join(ch for ch in phone if ch.isdigit())
    if digits.startswith('0') and len(digits) == 10:
        return '94' + digits[1:]
    if digits.startswith('94') and len(digits) == 11:
        return digits
    return digits


def build_estimate_text(estimate) -> str:
    lines = [
        f"SL APEX RIDER - Service Estimate #{estimate.id} (BEFORE service)",
        f"Customer: {estimate.customer.name}",
    ]
    if estimate.motorcycle_id:
        lines.append(f"Bike: {estimate.motorcycle.plate_no} ({estimate.motorcycle.brand} {estimate.motorcycle.model})")
    lines.append(f"Date: {estimate.created_at:%Y-%m-%d %H:%M}")
    lines.append("--------------------------")
    for item in estimate.items.select_related('part').all():
        lines.append(f"{item.part.name} x{item.qty} @ Rs.{item.unit_price} = Rs.{item.unit_price * item.qty}")
    if estimate.service_note:
        lines.append(f"Service: {estimate.service_note}")
    if estimate.labour_charge:
        lines.append(f"Labour: Rs.{estimate.labour_charge}")
    lines += ["--------------------------", f"ESTIMATED TOTAL: Rs.{estimate.total}",
              "Reply OK to approve. - SL APEX RIDER, Mihinthale"]
    return "\n".join(lines)


def build_completion_text(estimate) -> str:
    bike = estimate.motorcycle.plate_no if estimate.motorcycle_id else "your bike"
    return "\n".join([
        "SL APEX RIDER - Service Done!",
        f"Customer: {estimate.customer.name}",
        f"Bike {bike} is ready for pickup.",
        f"Service: {estimate.service_note or '-'}",
        f"Total: Rs.{estimate.total}",
        "Thank you! - SL APEX RIDER, Mihinthale",
    ])


def build_bill_text(sale) -> str:
    lines = [
        f"SL APEX RIDER - Bill #{sale.id}",
        f"Customer: {sale.customer.name}",
        f"Date: {sale.date:%Y-%m-%d %H:%M}",
        "--------------------------",
    ]
    for item in sale.items.select_related('part').all():
        lines.append(f"{item.part.name} x{item.qty} @ Rs.{item.unit_price} = Rs.{item.unit_price * item.qty}")
    if sale.service_note:
        lines.append(f"Service: {sale.service_note}")
    if sale.labour_charge:
        lines.append(f"Labour: Rs.{sale.labour_charge}")
    lines += ["--------------------------", f"TOTAL: Rs.{sale.total}", "Thank you! - SL APEX RIDER, Mihinthale"]
    return "\n".join(lines)
