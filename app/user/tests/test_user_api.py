"""
Testing the user endpoints / API.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")


def create_user(**params):
    """Create and return a new user."""

    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):

    """Test Public features of the user API."""

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "email": "test@example.com",
            "password": "pass123",
            "name": "User Name",
        }

    def test_create_user_success(self):
        """Test the successful user creation cases."""

        res = self.client.post(CREATE_USER_URL, self.payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=self.payload["email"])
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertNotIn("password", res.data)

    def test_error_when_user_exists(self):
        """Test error is returned if user with email exists."""

        create_user(**self.payload)

        res = self.client.post(CREATE_USER_URL, self.payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test that created password less than 5 raises error."""

        ch_payload = self.payload.copy()
        ch_payload["password"] = "ps"

        res = self.client.post(CREATE_USER_URL, ch_payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        check_created = (
            get_user_model().objects.filter(email=ch_payload["email"]).exists()
        )

        self.assertFalse(check_created)
