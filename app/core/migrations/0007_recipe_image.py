# Generated by Django 3.2.18 on 2023-03-30 14:02

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_auto_20230329_1305"),
    ]

    operations = [
        migrations.AddField(
            model_name="recipe",
            name="image",
            field=models.ImageField(
                null=True, upload_to=core.models.recipe_image_file_path
            ),
        ),
    ]