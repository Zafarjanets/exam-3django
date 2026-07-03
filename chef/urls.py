from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('set-language/', views.set_language, name='set_language'),
    path('search/', views.recipe_search, name='recipe_search'),
    path('image/', views.image_search, name='image_search'),
    path('dish/<int:dish_id>/', views.ai_dish_detail, name='ai_dish_detail'),
    path('dish/<int:dish_id>/favorite/', views.add_ai_favorite, name='add_ai_favorite'),
    path('favorites/', views.favorites, name='favorites'),
    path('favorite/add/<int:recipe_id>/', views.add_favorite, name='add_favorite'),
    path('favorite/remove/<int:recipe_id>/', views.remove_favorite, name='remove_favorite'),
    path('history/', views.history, name='history'),
    path('history/clear/', views.clear_history, name='clear_history'),
    path('profile/', views.profile, name='profile'),
    
    # Weekly Meal Planner URLs
    path('meal-planner/', views.weekly_meal_planner, name='weekly_meal_planner'),
    path('meal-plans/', views.meal_plans_history, name='meal_plans_history'),
    path('meal-plan/<int:plan_id>/', views.meal_plan_detail, name='meal_plan_detail'),
    path('meal-plan/<int:plan_id>/delete/', views.delete_meal_plan, name='delete_meal_plan'),
    path('meal-plan/<int:plan_id>/permanent-delete/', views.meal_plan_permanent_delete, name='meal_plan_permanent_delete'),
    path('meal-plan/<int:plan_id>/regenerate/', views.regenerate_meal_plan, name='regenerate_meal_plan'),
]