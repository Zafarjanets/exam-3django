from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    DIFFICULTY_CHOICES = [('easy', 'Easy'),('medium', 'Medium'),('hard', 'Hard'),]
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField()
    cooking_time = models.PositiveIntegerField(help_text='Cooking time in minutes')
    servings = models.PositiveIntegerField(default=1)
    difficulty = models.CharField(max_length=10,choices=DIFFICULTY_CHOICES,default='easy')
    image = models.ImageField(upload_to='recipes/',blank=True,null=True)
    ingredients = models.ManyToManyField(Ingredient,through='RecipeIngredient',related_name='recipes')
    created_by = models.ForeignKey( settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='recipes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe,on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient,on_delete=models.CASCADE)
    quantity = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.ingredient.name} ({self.quantity})'


class Favorite(models.Model):
    user = models.ForeignKey( settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'recipe')
        
    def __str__(self):
        return f'{self.user.username} - {self.recipe.title}'


class AIRecipeRequest(models.Model):
    user = models.ForeignKey( settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    ingredients_text = models.TextField(blank=True,null=True,help_text='Products entered by user')
    image = models.ImageField(upload_to='ingredient_images/',blank=True,null=True)
    detected_ingredients = models.TextField(blank=True,null=True)
    ai_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'AI Request #{self.id}'


class AIDishSuggestion(models.Model):
    ai_request = models.ForeignKey(
        AIRecipeRequest,
        on_delete=models.CASCADE,
        related_name='dishes',
        null=True,
        blank=True,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    summary = models.TextField()
    instructions = models.TextField()
    ingredients_text = models.TextField(blank=True)
    cooking_time = models.PositiveIntegerField(default=30)
    difficulty = models.CharField(
        max_length=10,
        choices=Recipe.DIFFICULTY_CHOICES,
        default='easy',
    )
    saved_recipe = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_suggestions',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_favorited(self):
        return self.saved_recipe_id is not None

    def get_video_links(self):
        from .utils import build_cooking_video_links
        return build_cooking_video_links(self.title, self.ingredients_text)

    @property
    def photo_url(self):
        """Get a relevant food photo URL based on the dish title."""
        import urllib.parse
        search_term = urllib.parse.quote(self.title)
        # Use Unsplash source for random food photos based on search term
        return f"https://source.unsplash.com/600x400/?{search_term},food,cooking"

class Review(models.Model):
    user = models.ForeignKey( settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,on_delete=models.CASCADE,related_name='reviews')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.recipe.title}'