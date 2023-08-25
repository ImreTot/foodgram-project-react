from djoser.serializers import UserCreateSerializer, UserSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers

from recipes.models import (Tag, Ingredient, Recipe, RecipeIngredient,
                            Favorite, Subscription, ShoppingCart)

User = get_user_model()


class CustomUserCreateSerializer(UserCreateSerializer):
    """
    Custom user serializer replaces standard djoser serializer
    with additional fields 'first_name', 'last_name'.
    """
    class Meta:
        model = User
        fields = ('email', 'id', 'password', 'username',
                  'first_name', 'last_name')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed',)

    def get_is_subscribed(self, obj):
        request = self.context['request']
        user = request.user
        return Subscription.objects.filter(
            follower=user, following=obj).exists()


class SubscriptionSerializer(CustomUserSerializer):
    email = serializers.ReadOnlyField()
    username = serializers.ReadOnlyField()
    first_name = serializers.ReadOnlyField()
    last_name = serializers.ReadOnlyField()
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed',
                  'recipes', 'recipes_count')

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        serializer = RecipeInSubscriptionSerializer(recipes, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        recipes = obj.recipes.all()
        recipes_numbers = recipes.count()
        return recipes_numbers


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def get_amount(self, obj):
        recipe_ingredients = RecipeIngredient.objects.get(
            recipe=self.context['recipe'],
            ingredient=obj
        )
        return recipe_ingredients.amount


class RecipeSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')

    def get_user(self):
        request = self.context.get('request')
        user = request.user
        return user

    def get_tags(self, obj):
        if self.context['request'].method == 'POST':
            return [tag.id for tag in obj.tags.all()]
        tags = TagSerializer(obj.tags.all(), many=True)
        return tags.data


    def get_author(self, obj):
        author = obj.author
        author_serializer = CustomUserSerializer(
            author,
            context=self.context
        )
        return author_serializer.data

    def get_ingredients(self, obj):
        ingredients = obj.ingredients.all()
        self.context['recipe'] = obj
        serializer = IngredientInRecipeSerializer(
            ingredients,
            many=True,
            context=self.context
        )
        return serializer.data

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = request.user
        if user.is_authenticated:
            return Favorite.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.get_user()
        if user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=user, recipe=obj
            ).exists()
        return False


class RecipeInSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only = '__all__'
