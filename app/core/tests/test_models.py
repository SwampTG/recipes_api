"""
Tests for models.
"""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


def create_user(email="user@example.com", password="pass123"):
    """Creates a user with the model"""

    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    """Testing models"""

    def test_create_user_with_email_successful(self):
        """Test creating user with correct credentials"""
        email = "test@example.com"
        password = "testpass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)

        # Using check_password Because it's a Hashed password
        self.assertTrue(user.check_password(password))

    def test_new_email_normalized(self):
        """Test email is normalized for newly created users"""
        sample_emails = [
            ["test1@EXAMPLE.COM", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, "password123")
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_error(self):
        """Test that creating a user without an email should raise an error."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, "password123")

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "password123")

    def test_create_super_user(self):
        """Test that a superuser is created."""
        user = get_user_model().objects.create_superuser(
            "test@example.com",
            "pass123",
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        """Test creating a recipe sucessfully"""

        user = get_user_model().objects.create_user(
            "test@example.com",
            "password123",
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample Title",
            time_minutes=5,
            price=Decimal("5.50"),
            description="Sample desc",
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test creating a tag is sucessful"""

        user = create_user()
        tag = models.Tag.objects.create(user=user, name="Tag1")

        self.assertEqual(str(tag), tag.name)
        self.assertEqual(tag.user, user)

    def test_create_ingredient(self):
        """Test creating a Ingredient is Successful"""

        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name="One Ingredient",
        )

        self.assertEqual(str(ingredient), ingredient.name)

    @patch("core.models.uuid.uuid4")
    def test_recipe_file_name_uuid(self, mocked_uuid):
        """Test generating image path."""

        uuid = "test-uuid"
        mocked_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, "example.jpg")

        self.assertEqual(file_path, f"uploads/recipe/{uuid}.jpg")
