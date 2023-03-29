"""
Tests for the tags API.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer


TAGS_URL = reverse("recipe:tag-list")


def get_detail_url(tag_id):
    """Return tag detail url for an id"""
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email="user@example.com", password="pass123"):
    """Create and return a user."""

    return get_user_model().objects.create(email=email, password=password)


class PublicTagsApiTests(TestCase):
    """Test unaunthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags."""

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""

        Tag.objects.create(user=self.user, name="Curinthia")
        Tag.objects.create(user=self.user, name="Framengo")

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by("-name")
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_filtered_tags_for_user(self):
        """Test that list of tags is limited to user"""

        user2 = create_user(email="user2@example.com")
        tag = Tag.objects.create(user=user2, name="Rapid")
        _ = Tag.objects.create(user=self.user, name="Fruity")
        self.client.force_authenticate(user2)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        """Test updating TAG."""

        tag = Tag.objects.create(user=self.user, name="Dissert")

        payload = {"name": "After Dinner"}
        url = get_detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        """Test deleting TAG."""

        tag = Tag.objects.create(user=self.user, name="Breakfast")

        res = self.client.delete(get_detail_url(tag.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)

        self.assertFalse(tags.exists())
