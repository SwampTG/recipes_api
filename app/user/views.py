"""
Views for User API.
"""

from rest_framework import generics

from user.serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):

    """Creates a new user in the database."""

    serializer_class = UserSerializer
