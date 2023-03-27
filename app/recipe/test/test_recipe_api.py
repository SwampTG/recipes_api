"""
Tests for recipe APIs.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return detail of specific recipe."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **kwargs):
    """Create and return recipe instance."""

    defaults = {
        "title": "Test Recipe",
        "time_minutes": 22,
        "price": Decimal("5.25"),
        "description": "Sample description",
        "link": "http://example.com/recipe.pdf",
    }
    defaults.update(kwargs)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**kwargs):
    return get_user_model().objects.create_user(**kwargs)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that auth is required for the endpoint."""

        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="user@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving recipes list."""

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limited to authenticated user."""

        other_user = create_user(
            email="different@user.com",
            password="password123",
        )

        create_recipe(user=other_user, description="Changed Description")
        create_recipe(user=self.user, description="Another description")

        self.client.force_authenticate(other_user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=other_user).order_by("id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0], serializer.data[0])

    def test_get_recipe_detail(self):
        """Test get recipe detail."""

        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        """Test creating a recipe."""

        payload = {
            "title": "Sample",
            "time_minutes": 30,
            "price": Decimal("5.99"),
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.filter(id=res.data["id"])[0]

        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test the partial update."""
        original_link = "https://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="Sample title",
            link=original_link,
        )

        payload = {"title": "Changed title"}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        recipe = create_recipe(
            user=self.user,
            title="Sample Recipe Title",
            link="https://example.com/recipe.pdf",
            description="Sample recipe description.",
        )

        payload = {
            "title": "New Recipe title",
            "link": "https://example.com/new-recipe.pdf",
            "time_minutes": 10,
            "price": Decimal("2.50"),
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_update_user_return_error(self):
        new_user = create_user(
            email="newusertest@example.com", password="test123"
        )
        recipe = create_recipe(user=self.user)

        payload = {"user": new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

        def test_delete_recipe(self):
            """Test deleting a recipe."""

            recipe = create_recipe(user=self.user)

            url = detail_url(recipe.id)
            res = self.client.delete(url)

            self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
            self.assertFalse(Recipe.objects.filtes(id=recipe.id).exists())

        def test_recipe_other_user_recipe_error(self):
            """Test trying to delete another users recipe gives error."""

            new_user = create_user(
                email="user2newtest@example.com", password="test123"
            )
            recipe = create_recipe(user=new_user)

            url = detail_url(recipe.id)
            res = self.client.delete(url)

            self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
            self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
