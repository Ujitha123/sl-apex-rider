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
    """Record of a bill sent (or queued) to the customer's mobile."""
    CHANNEL_CHOICES = [('whatsapp', 'WhatsApp'), ('sms', 'SMS')]
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='bill_messages')
    phone = models.CharField(max_length=20)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES, default='whatsapp')
    body = models.TextField()
    status = models.CharField(max_length=20, default='logged')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bill #{self.sale_id} → {self.phone} via {self.channel} ({self.status})"


def normalize_lk_mobile(phone: str) -> str:
    """07XXXXXXXX → 947XXXXXXXX for wa.me links. Leaves other formats untouched."""
    digits = ''.join(ch for ch in phone if ch.isdigit())
    if digits.startswith('0') and len(digits) == 10:
        return '94' + digits[1:]
    if digits.startswith('94') and len(digits) == 11:
        return digits
    return digits


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
