from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SparePart(models.Model):
    name = models.CharField(max_length=150)
    part_number = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='parts')
    brand = models.CharField(max_length=100, blank=True)
    compatible_models = models.TextField(help_text="Comma separated e.g. Honda CB150, Yamaha FZ")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_qty = models.PositiveIntegerField(default=0)
    min_stock = models.PositiveIntegerField(default=5)
    description = models.TextField(blank=True)
    negotiable = models.BooleanField(default=False, help_text="Tick if price can be negotiated at sale time")
    service_interval_km = models.PositiveIntegerField(default=2500,
        help_text="Km interval for predictive maintenance, e.g. 2500 for engine oil")

    @property
    def is_low_stock(self):
        return self.stock_qty <= self.min_stock

    def matches_bike(self, bike_model: str):
        return bike_model.lower() in self.compatible_models.lower()

    def __str__(self):
        return f"{self.name} ({self.part_number})"
