from django.db import models
from customers.models import Customer


class Motorcycle(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='motorcycles')
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    plate_no = models.CharField(max_length=20, unique=True)
    mileage = models.PositiveIntegerField(default=0, help_text="Current odometer in km")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model} - {self.plate_no}"
