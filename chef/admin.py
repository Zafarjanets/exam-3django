from django.contrib import admin
from .models import (
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    AIRecipeRequest,
    AIDishSuggestion,
    Review,
    WeeklyMealPlan,
    DailyMeal
    )
admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)
admin.site.register(Favorite)
admin.site.register(AIRecipeRequest)
admin.site.register(AIDishSuggestion)
admin.site.register(Review)
admin.site.register(WeeklyMealPlan)
admin.site.register(DailyMeal)