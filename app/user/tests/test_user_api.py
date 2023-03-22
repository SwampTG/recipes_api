"""
Testing the user endpoints / API.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status


CREATE_USER_URL = reverse("user:create")
GET_TOKEN_URL = reverse("user:token")


def create_user(**params):
    """Create and return a new user."""

    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):

    """Test Public features of the user API."""

    def setUp(self):
        self.client = APIClient()
        self.user_data_payload = {
            "email": "test@example.com",
            "password": "pass123",
            "name": "User Name",
        }

    def test_create_user_success(self):
        """Test the successful user creation cases."""

        res = self.client.post(CREATE_USER_URL, self.user_data_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(
                email=self.user_data_payload["email"])

        self.assertTrue(user.check_password(
            self.user_data_payload["password"]))

        self.assertNotIn("password", res.data)

    def test_error_when_user_exists(self):
        """Test error is returned if user with email exists."""

        create_user(**self.user_data_payload)

        res = self.client.post(CREATE_USER_URL, self.user_data_payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test that created password less than 5 raises error."""

        ch_payload = {
            'email': 'wrong@example.test',
            'password': "ps",
        }

        res = self.client.post(CREATE_USER_URL, ch_payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        check_created = (
            get_user_model().objects.filter(email=ch_payload["email"]).exists()
        )

        self.assertFalse(check_created)

    def test_token_session_creation(self):
        """Test generates token for valid credentials."""

        user_data_payload = {
            'name': 'Test Name',
            'email': 'test@example.com',
            'password': 'test-user-password123',
        }

        auth_payload = {
            "email": user_data_payload["email"],
            "password": user_data_payload["password"],
        }

        create_user(**user_data_payload)

        res = self.client.post(GET_TOKEN_URL, auth_payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error for invalid credentials."""

        create_user(**self.user_data_payload)
        wrong_payload = {"email": "wrong@email.com", "password": "aabbcc"}
        res = self.client.post(GET_TOKEN_URL, wrong_payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_error_for_blank_password(self):
        """Test that no blank password should be authenticated."""

        nopass_payload = {
            "email": self.user_data_payload["email"],
            "password": ""
        }

        res = self.client.post(GET_TOKEN_URL, nopass_payload)

        self.assertNotIn("token", res.data)
        self.assertTrue(res.status_code, status.HTTP_400_BAD_REQUEST)
