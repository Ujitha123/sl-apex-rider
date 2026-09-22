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
