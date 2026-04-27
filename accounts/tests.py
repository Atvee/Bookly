from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Profile


class ProfileSignalTests(TestCase):
    def test_profile_is_created_for_new_user(self):
        user = get_user_model().objects.create_user(username="reader", password="pass")

        self.assertEqual(user.profile.role, Profile.Role.MEMBER)
        self.assertTrue(user.profile.library_id.startswith("LIB-"))

    def test_staff_user_gets_admin_role(self):
        user = get_user_model().objects.create_user(username="staff", password="pass", is_staff=True)

        self.assertEqual(user.profile.role, Profile.Role.ADMIN)
