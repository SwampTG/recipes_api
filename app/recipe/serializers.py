"""
Serializers for recipe APIs.
"""
from rest_framework import serializers

from core.models import Recipe, Tag, Ingredient


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for ingredients."""

    class Meta:
        model = Ingredient
        fields = [
            "id",
            "name",
        ]
        read_only_fields = [
            "id",
        ]


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tags created by users"""

    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
        ]
        read_only_fields = [
            "id",
        ]


class RecipeSerializer(serializers.ModelSerializer):
    """Serializers for Recipe API."""

    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "time_minutes",
            "price",
            "link",
            "tags",
            "ingredients",
        ]
        read_only_fields = ["id"]

    def _get_or_create_ingredients(self, ings, recipe):
        """Create or return ingredients for recipe."""

        auth_user = self.context["request"].user
        for ing in ings:
            ing_instance, _ = Ingredient.objects.get_or_create(
                user=auth_user,
                **ing,
            )
            recipe.ingredients.add(ing_instance)

    def _get_or_create_tags(self, tags, recipe):
        """Create or return a tag as needed."""

        auth_user = self.context["request"].user
        for tag in tags:
            tag_obj, _ = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )

            recipe.tags.add(tag_obj)

    def create(self, validated_data):
        """Create a recipe."""
        tags = validated_data.pop("tags", [])
        ingredients = validated_data.pop("ingredients", [])

        recipe = Recipe.objects.create(**validated_data)

        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        """Update recipe."""

        tags = validated_data.pop("tags", None)
        ingredients = validated_data.pop("ingredients", None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

        if ingredients is not None:
            instance.ingredients.clear()
            self._get_or_create_ingredients(ingredients, instance)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        instance.save()
        return instance


class RecipeDetailSerializer(RecipeSerializer):
    """Show one recipe with more details."""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ["description", "image"]


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for recipe image upload."""

    class Meta:
        model = Recipe
        fields = ["id", "image"]
        read_only_fields = ["id"]
        extra_kwargs = {"image": {"required": "True"}}
