from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Customer


class CustomerModelTests(TestCase):
    def test_str_includes_name_and_phone(self):
        c = Customer.objects.create(name="Nimal Perera", phone="0771234567")
        self.assertEqual(str(c), "Nimal Perera (0771234567)")


class CustomerViewAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="pass12345")

    def test_customer_list_requires_login(self):
        resp = self.client.get(reverse('customer-list'))
        self.assertEqual(resp.status_code, 302)  # redirected to login

    def test_customer_list_accessible_when_logged_in(self):
        self.client.login(username="staff", password="pass12345")
        resp = self.client.get(reverse('customer-list'))
        self.assertEqual(resp.status_code, 200)
