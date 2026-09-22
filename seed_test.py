"""
Seed script for manual / UAT testing (Weeks 17-18).

Usage:
    python manage.py shell < seed_test.py

Creates a test staff login (staff / pass12345), a couple of customers,
motorcycles, spare parts and a service record so the dashboard, bike detail,
compatibility and predictive-alert pages all have something to show.
Safe to run multiple times — uses get_or_create throughout.
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from customers.models import Customer
from motorcycles.models import Motorcycle
from inventory.models import Category, SparePart
from maintenance.models import ServiceRecord, generate_predictions

# 1. Test login for UAT
user, created = User.objects.get_or_create(username='staff', defaults={'is_staff': True})
if created:
    user.set_password('pass12345')
    user.save()
    print('Created test user: staff / pass12345')
else:
    print('Test user "staff" already exists')

# 2. Customers
kamal, _ = Customer.objects.get_or_create(
    name='Kamal Silva', phone='0771234567',
    defaults={'email': 'kamal@example.com', 'address': 'Mihinthale'},
)
nadeesha, _ = Customer.objects.get_or_create(
    name='Nadeesha Fernando', phone='0779876543',
    defaults={'email': 'nadeesha@example.com', 'address': 'Anuradhapura'},
)

# 3. Motorcycles
bike1, _ = Motorcycle.objects.get_or_create(
    plate_no='WP-CAB-1234',
    defaults={'customer': kamal, 'brand': 'Yamaha', 'model': 'FZ', 'year': 2022, 'mileage': 2400},
)
bike2, _ = Motorcycle.objects.get_or_create(
    plate_no='NC-QRS-5678',
    defaults={'customer': nadeesha, 'brand': 'Honda', 'model': 'CB150', 'year': 2021, 'mileage': 7800},
)

# 4. Spare parts
cat, _ = Category.objects.get_or_create(name='Engine')
SparePart.objects.get_or_create(
    part_number='ENG-OIL-01',
    defaults={
        'name': 'Engine Oil 20W-40', 'category': cat, 'brand': 'Motul',
        'compatible_models': 'Yamaha FZ, Honda CB150', 'price': '1800.00',
        'stock_qty': 15, 'min_stock': 5, 'service_interval_km': 2500,
    },
)
SparePart.objects.get_or_create(
    part_number='AIR-FLT-01',
    defaults={
        'name': 'Air Filter', 'category': cat, 'brand': 'OEM',
        'compatible_models': 'Yamaha FZ', 'price': '950.00',
        'stock_qty': 3, 'min_stock': 5, 'service_interval_km': 6000,  # deliberately low stock
    },
)

# 5. A past service record so predictive alerts have a baseline
ServiceRecord.objects.get_or_create(
    motorcycle=bike1, customer=kamal, mileage=2200,
    defaults={'description': 'Routine service', 'parts_replaced': 'Engine Oil'},
)

# 6. Generate predictive alerts for both bikes
for bike in (bike1, bike2):
    alerts = generate_predictions(bike)
    print(f'{bike}: {len(alerts)} predictive alert(s) generated')

print('\nSeed complete. Log in with staff / pass12345 and visit http://127.0.0.1:8000/')
