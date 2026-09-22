from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer
from .models import Motorcycle


class MotorcycleModelTests(TestCase):
    def test_str_includes_brand_model_plate(self):
        cust = Customer.objects.create(name="Kamal", phone="0711111111")
        bike = Motorcycle.objects.create(
            customer=cust, brand="Yamaha", model="FZ", year=2022,
            plate_no="ABC-1234", mileage=5000,
        )
        self.assertEqual(str(bike), "Yamaha FZ - ABC-1234")


class MotorcycleViewAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="pass12345")

    def test_bike_list_requires_login(self):
        resp = self.client.get(reverse('bike-list'))
        self.assertEqual(resp.status_code, 302)

    def test_bike_list_accessible_when_logged_in(self):
        self.client.login(username="staff", password="pass12345")
        resp = self.client.get(reverse('bike-list'))
        self.assertEqual(resp.status_code, 200)
