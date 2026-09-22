from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class DashboardAuthTests(TestCase):
    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 302)

    def test_dashboard_accessible_when_logged_in(self):
        User.objects.create_user(username="staff", password="pass12345")
        self.client.login(username="staff", password="pass12345")
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
