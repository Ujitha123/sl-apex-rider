from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer
from motorcycles.models import Motorcycle
from .models import ServiceRecord, PredictiveAlert, generate_predictions


class PredictiveMaintenanceTests(TestCase):
    def setUp(self):
        self.cust = Customer.objects.create(name="Sunil", phone="0722222222")
        self.bike = Motorcycle.objects.create(
            customer=self.cust, brand="Honda", model="CB150", year=2021,
            plate_no="XYZ-9999", mileage=500,
        )

    def test_no_alert_when_far_from_due_mileage(self):
        alerts = generate_predictions(self.bike)
        self.assertEqual(len(alerts), 0)

    def test_alert_created_within_early_warning_window(self):
        # Oil change interval is 2500km; put the bike at 2400km -> within 500km warning
        self.bike.mileage = 2400
        self.bike.save()
        alerts = generate_predictions(self.bike)
        self.assertTrue(any(a.predicted_part == "Engine Oil" for a in alerts))

    def test_alert_not_duplicated_on_repeat_call(self):
        generate_predictions(self.bike)
        count_after_first = PredictiveAlert.objects.filter(motorcycle=self.bike).count()
        generate_predictions(self.bike)
        count_after_second = PredictiveAlert.objects.filter(motorcycle=self.bike).count()
        self.assertEqual(count_after_first, count_after_second)


class MaintenanceViewAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="pass12345")

    def test_service_list_requires_login(self):
        resp = self.client.get(reverse('service-list'))
        self.assertEqual(resp.status_code, 302)

    def test_alerts_list_requires_login(self):
        resp = self.client.get(reverse('alert-list'))
        self.assertEqual(resp.status_code, 302)
