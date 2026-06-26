from django.contrib import admin
from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    AIRecipeRequest,
    Review
    )
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)
admin.site.register(Favorite)
admin.site.register(AIRecipeRequest)
admin.site.register(Review)