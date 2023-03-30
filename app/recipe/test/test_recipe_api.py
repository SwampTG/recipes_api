"""
Tests for recipe APIs.
"""

from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """Create and return detail of specific recipe."""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """Create and return an image upload URL."""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


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

        recipes = Recipe.objects.all().order_by("-id")
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

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user).order_by("id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

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
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

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

    def test_create_recipe_with_new_tag(self):
        """Test creating recipe already with Tags."""

        payload = {
            "title": "Thai Prawn Curry",
            "time_minutes": 30,
            "price": Decimal("2.50"),
            "tags": [{"name": "Thai"}, {"name": "Dinner"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]

        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"], user=self.user
            ).exists()
            self.assertTrue(exists)

    def test_creating_recipes_with_existing_tags(self):
        """Test creating a recipe with existing TAGs."""

        tag_indian = Tag.objects.create(name="Indian", user=self.user)
        payload = {
            "title": "Pongal",
            "time_minutes": 60,
            "price": Decimal("25.00"),
            "tags": [{"name": "Indian"}, {"name": "Breakfast"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())

        for tag in payload["tags"]:
            exists = recipe.tags.filter(
                name=tag["name"], user=self.user
            ).exists()

            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """Test creating TAG when updating a recipe."""

        recipe = create_recipe(user=self.user)

        payload = {"tags": [{"name": "Lunch"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name="Lunch")
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe"""

        tag_breakfast = Tag.objects.create(name="Pão na Chapa", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")
        payload = {"tags": [{"name": "Lunch"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_clear_recipe_tag(self):
        """Test deleting all tags of specific recipe."""

        tag = Tag.objects.create(user=self.user, name="Example Tag")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        payload = {"tags": []}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_ingredient_through_recipe(self):
        """Test that ingredients are created with recipe"""

        payload = {
            "title": "Cauliflower Tacos",
            "time_minutes": 60,
            "price": Decimal("10.5"),
            "ingredients": [
                {"name": "Cauliflower"},
                {"name": "Salt"},
            ],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)

        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_existing_ingredient(self):
        """Test creating a new recipe with existing ingredient."""

        ingredient = Ingredient.objects.create(user=self.user, name="Lemon")

        payload = {
            "title": "Sample",
            "time_minutes": 25,
            "price": Decimal("10.36"),
            "ingredients": [{"name": "Lemon"}, {"name": "Fish Sauce"}],
        }

        res = self.client.post(RECIPES_URL, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)

        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())

        for ingredient in payload["ingredients"]:
            exists = recipe.ingredients.filter(
                name=ingredient["name"],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_creating_ingredient_on_update(self):
        """Test creating the ingredient if recipe is updated."""

        recipe = create_recipe(user=self.user)

        payload = {"ingredients": [{"name": "Limes"}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        new_ingredient = Ingredient.objects.filter(
            user=self.user, name=payload["ingredients"][0]["name"]
        )
        self.assertIn(new_ingredient[0], recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test putting existing ingredient on recipe update."""

        ingredient1 = Ingredient.objects.create(user=self.user, name="Pepper")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name="Chilli")
        payload = {"ingredients": [{"name": ingredient2.name}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clearing_ingredients_on_recipe(self):
        ingredient = Ingredient.objects.create(name="Garlic", user=self.user)
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {"ingredients": []}
        url = detail_url(recipe.id)

        res = self.client.patch(url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)


class ImageUploadTests(TestCase):
    """Tests for the Image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email="user_test@example.com", password="pass123"
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a Recipe."""

        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_f:
            img = Image.new(
                "RGB",
                (
                    10,
                    10,
                ),
            )
            img.save(image_f, format="JPEG")
            image_f.seek(0)
            payload = {"image": image_f}
            res = self.client.post(url, payload, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def upload_image_bad_request(self):
        """Test uploading invalid image."""

        url = image_upload_url(self.recipe.id)
        payload = {"image": "astringinsteadofimage"}
        res = self.client.post(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
