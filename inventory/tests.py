from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import SparePart


class SparePartModelTests(TestCase):
    def test_is_low_stock_true_when_at_or_below_minimum(self):
        part = SparePart.objects.create(
            name="Engine Oil", part_number="P-001", compatible_models="Yamaha FZ",
            price="1500.00", stock_qty=3, min_stock=5,
        )
        self.assertTrue(part.is_low_stock)

    def test_is_low_stock_false_when_above_minimum(self):
        part = SparePart.objects.create(
            name="Engine Oil", part_number="P-002", compatible_models="Yamaha FZ",
            price="1500.00", stock_qty=10, min_stock=5,
        )
        self.assertFalse(part.is_low_stock)

    def test_matches_bike_is_case_insensitive(self):
        part = SparePart.objects.create(
            name="Brake Pads", part_number="P-003",
            compatible_models="Honda CB150, Yamaha FZ", price="800.00",
        )
        self.assertTrue(part.matches_bike("yamaha fz"))
        self.assertFalse(part.matches_bike("suzuki gixxer"))


class InventoryViewAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="pass12345")

    def test_part_list_requires_login(self):
        resp = self.client.get(reverse('part-list'))
        self.assertEqual(resp.status_code, 302)

    def test_part_list_accessible_when_logged_in(self):
        self.client.login(username="staff", password="pass12345")
        resp = self.client.get(reverse('part-list'))
        self.assertEqual(resp.status_code, 200)
