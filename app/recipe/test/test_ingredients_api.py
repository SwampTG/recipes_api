"""
Tests for Ingredients API.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse("recipe:ingredient-list")


def get_detail_url(ingredient_id):
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


def create_user(email="example_user@test.com", password="testpass123"):
    return get_user_model().objects.create_user(email=email, password=password)


def create_ingredient(name="Test Ingredient", user=None):
    if not user:
        user = create_user()

    return Ingredient.objects.create(name=name, user=user)


class PublicAPITests(TestCase):
    """Test Unauthenticated API calls."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_is_required_for_ingredients(self):
        """Testing auth for ingredients"""

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedAPITests(TestCase):
    """Test for autheticated user Requests on Ingredients."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient(self):
        """Test retrieving list of ingredients."""

        create_ingredient("Kale", user=self.user)
        create_ingredient("Vanilla", user=self.user)

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by("-name")
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_access(self):
        """Test list is limited to user."""

        user2 = create_user(email="user2@example.com")
        create_ingredient(user=user2, name="Salt")
        ingredient = create_ingredient(name="Pepper", user=self.user)

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)
        self.assertEqual(res.data[0]["id"], ingredient.id)

    def test_update_ingredient(self):
        """Test get specific ingredient by id."""

        ingredient = create_ingredient(user=self.user, name="Cilantro")

        payload = {"name": "Coriander"}
        url = get_detail_url(ingredient.id)

        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        """Test deleting an ingredient."""

        ingredient = create_ingredient(user=self.user, name="Lettuce")
        url = get_detail_url(ingredient.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertNotIn(ingredient, Ingredient.objects.all())
