from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardAccessTests(TestCase):
    def test_member_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboards:user_dashboard"))

        self.assertEqual(response.status_code, 302)

    def test_member_dashboard_loads_for_user(self):
        get_user_model().objects.create_user(username="member", password="MemberPass123!")
        self.client.login(username="member", password="MemberPass123!")
        response = self.client.get(reverse("dashboards:user_dashboard"))

        self.assertEqual(response.status_code, 200)
