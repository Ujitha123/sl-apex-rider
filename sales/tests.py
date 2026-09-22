from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer
from inventory.models import SparePart
from .models import Sale


class SaleCreationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="pass12345")
        self.client.login(username="staff", password="pass12345")
        self.cust = Customer.objects.create(name="Amara", phone="0733333333")
        self.part = SparePart.objects.create(
            name="Chain & Sprocket", part_number="P-010",
            compatible_models="Yamaha FZ", price="4500.00", stock_qty=10,
        )

    def test_sale_deducts_stock_and_sets_total(self):
        resp = self.client.post(reverse('sale-add'), {
            'customer': self.cust.id,
            f'qty_{self.part.id}': 2,
        })
        self.assertEqual(resp.status_code, 302)
        self.part.refresh_from_db()
        self.assertEqual(self.part.stock_qty, 8)
        sale = Sale.objects.latest('id')
        self.assertEqual(sale.total, Decimal('9000.00'))

    def test_sale_rejects_quantity_over_stock(self):
        resp = self.client.post(reverse('sale-add'), {
            'customer': self.cust.id,
            f'qty_{self.part.id}': 999,
        })
        self.assertEqual(resp.status_code, 200)  # re-renders form with error
        self.part.refresh_from_db()
        self.assertEqual(self.part.stock_qty, 10)  # unchanged
        self.assertEqual(Sale.objects.count(), 0)

    def test_sale_rejects_invalid_customer(self):
        resp = self.client.post(reverse('sale-add'), {
            'customer': 99999,
            f'qty_{self.part.id}': 1,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Sale.objects.count(), 0)

    def test_sale_list_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('sale-list'))
        self.assertEqual(resp.status_code, 302)
