from django.db import models
from customers.models import Customer
from motorcycles.models import Motorcycle


class ServiceRecord(models.Model):
    motorcycle = models.ForeignKey(Motorcycle, on_delete=models.CASCADE, related_name='services')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    service_date = models.DateField(auto_now_add=True)
    mileage = models.PositiveIntegerField(help_text="Odometer at service time")
    description = models.TextField()
    parts_replaced = models.TextField(blank=True)
    next_due_mileage = models.PositiveIntegerField(null=True, blank=True)
    next_due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.motorcycle.plate_no} @ {self.mileage}km"


class PredictiveAlert(models.Model):
    motorcycle = models.ForeignKey(Motorcycle, on_delete=models.CASCADE, related_name='alerts')
    predicted_part = models.CharField(max_length=150)
    reason = models.TextField()
    due_mileage = models.PositiveIntegerField()
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.motorcycle.plate_no}: {self.predicted_part} due @ {self.due_mileage}km"


# Mileage-based intervals for predictive maintenance (Objective 4)
MAINTENANCE_RULES = [
    {"part": "Engine Oil", "interval_km": 2500},
    {"part": "Air Filter", "interval_km": 6000},
    {"part": "Spark Plug", "interval_km": 8000},
    {"part": "Brake Pads", "interval_km": 8000},
    {"part": "Chain & Sprocket", "interval_km": 12000},
]


def generate_predictions(motorcycle):
    """Create PredictiveAlerts based on mileage + last service. Returns list."""
    last = motorcycle.services.order_by('-mileage').first()
    base_km = last.mileage if last else 0
    current = motorcycle.mileage
    alerts = []
    for rule in MAINTENANCE_RULES:
        due = base_km + rule["interval_km"]
        if current >= due - 500:  # 500km early warning
            obj, _ = PredictiveAlert.objects.get_or_create(
                motorcycle=motorcycle,
                predicted_part=rule["part"],
                due_mileage=due,
                is_done=False,
                defaults={"reason": f"Due every {rule['interval_km']}km. Last base {base_km}km, now {current}km."},
            )
            alerts.append(obj)
    return alerts
