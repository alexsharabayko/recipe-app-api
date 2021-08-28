from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECEPIES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """Return recipe detailed URL"""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def sample_tag(user, name='Main course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)

def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00,
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipiesApiTests(TestCase):
    """Test the publicly available recipe API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving recepies"""
        res = self.client.get(RECEPIES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipiesApiTests(TestCase):
    """Test the authorized user recepi API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'alex@sharky.com',
            'test_pass_q23',
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recepies(self):
        """Test retrieving recepies"""
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECEPIES_URL)

        recepies = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recepies, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recepies_limited_to_user(self):
        """Test that recepies returned are for authenticated user"""
        user2 = get_user_model().objects.create_user(
            'other@sharky.com',
            'test_pass_q23',
        )

        sample_recipe(user=user2)
        recipe = sample_recipe(user=self.user, title='Check title')

        res = self.client.get(RECEPIES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], recipe.title)

    def test_view_recipe_details(self):
        """Test view a recipe detailed info"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(self.user))
        recipe.ingredients.add(sample_ingredient(self.user))

        res = self.client.get(detail_url(recipe.id))

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
