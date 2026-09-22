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
            f'tick_{self.part.id}': '1',
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
            f'tick_{self.part.id}': '1',
            f'qty_{self.part.id}': 999,
        })
        self.assertEqual(resp.status_code, 200)  # re-renders form with error
        self.part.refresh_from_db()
        self.assertEqual(self.part.stock_qty, 10)  # unchanged
        self.assertEqual(Sale.objects.count(), 0)

    def test_sale_rejects_invalid_customer(self):
        resp = self.client.post(reverse('sale-add'), {
            'customer': 99999,
            f'tick_{self.part.id}': '1',
            f'qty_{self.part.id}': 1,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Sale.objects.count(), 0)

    def test_sale_list_requires_login(self):
        self.client.logout()
        resp = self.client.get(reverse('sale-list'))
        self.assertEqual(resp.status_code, 302)


class BillTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="pass12345")
        self.client.login(username="staff", password="pass12345")
        self.cust = Customer.objects.create(name="Bill Guy", phone="0711111111")
        self.part = SparePart.objects.create(
            name="Horn", part_number="BILL-01",
            compatible_models="Yamaha FZ", price="1100.00", stock_qty=5,
        )

    def _make_sale(self):
        resp = self.client.post(reverse('sale-add'), {
            'customer': self.cust.id,
            f'tick_{self.part.id}': '1',
            f'qty_{self.part.id}': 2,
            'labour': '500',
        })
        self.assertEqual(resp.status_code, 302)
        return Sale.objects.latest('id')

    def test_bill_page_requires_login(self):
        sale = self._make_sale()
        self.client.logout()
        self.assertEqual(self.client.get(reverse('sale-bill', args=[sale.id])).status_code, 302)

    def test_bill_page_shows_items_and_total(self):
        sale = self._make_sale()
        resp = self.client.get(reverse('sale-bill', args=[sale.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Horn')
        self.assertContains(resp, 'Rs. 2700')

    def test_whatsapp_send_logs_record(self):
        from .models import BillMessage
        sale = self._make_sale()
        resp = self.client.post(reverse('sale-send', args=[sale.id]), {'channel': 'whatsapp'})
        self.assertEqual(resp.status_code, 302)
        msg = BillMessage.objects.latest('id')
        self.assertEqual(msg.sale_id, sale.id)
        self.assertEqual(msg.channel, 'whatsapp')
        self.assertIn('TOTAL', msg.body)

    def test_sms_send_queues_without_gateway(self):
        from .models import BillMessage
        sale = self._make_sale()
        resp = self.client.post(reverse('sale-send', args=[sale.id]), {'channel': 'sms'})
        self.assertEqual(resp.status_code, 302)
        msg = BillMessage.objects.latest('id')
        self.assertEqual(msg.channel, 'sms')
        self.assertIn('queued', msg.status)


class EstimateFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="pass12345")
        self.client.login(username="staff", password="pass12345")
        self.cust = Customer.objects.create(name="Est Guy", phone="0722222222")
        self.part = SparePart.objects.create(
            name="Oil Filter", part_number="EST-01",
            compatible_models="Honda CB150", price="850.00", stock_qty=10,
        )

    def test_estimate_does_not_touch_stock_then_convert_does(self):
        from .models import Estimate, Sale
        resp = self.client.post(reverse('estimate-add'), {
            'customer': self.cust.id,
            f'tick_{self.part.id}': '1',
            f'qty_{self.part.id}': 2,
            'labour': '1000',
        })
        self.assertEqual(resp.status_code, 302)
        est = Estimate.objects.latest('id')
        from decimal import Decimal as D
        self.assertEqual(est.total, D('2700.00'))
        self.part.refresh_from_db()
        self.assertEqual(self.part.stock_qty, 10)  # untouched before service
        resp = self.client.post(reverse('estimate-convert', args=[est.id]))
        self.assertEqual(resp.status_code, 302)
        self.part.refresh_from_db()
        self.assertEqual(self.part.stock_qty, 8)
        est.refresh_from_db()
        self.assertIsNotNone(est.sale_id)
        self.assertEqual(Sale.objects.latest('id').id, est.sale_id)

    def test_estimate_send_and_completion_alert_logged(self):
        from .models import BillMessage
        self.client.post(reverse('estimate-add'), {
            'customer': self.cust.id,
            f'tick_{self.part.id}': '1',
            f'qty_{self.part.id}': 1,
        })
        from .models import Estimate
        est = Estimate.objects.latest('id')
        self.client.post(reverse('estimate-send', args=[est.id]), {'channel': 'sms'})
        self.client.post(reverse('estimate-complete', args=[est.id]), {'channel': 'sms'})
        kinds = list(BillMessage.objects.filter(estimate=est).values_list('kind', flat=True))
        self.assertIn('estimate', kinds)
        self.assertIn('completion_alert', kinds)
        est.refresh_from_db()
        self.assertEqual(est.status, 'completed')
