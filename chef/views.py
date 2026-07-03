from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import translation
from django.conf import settings
from groq import Groq
from .utils import detect_products, build_multi_dish_prompt, parse_ai_dishes
from .models import AIRecipeRequest, Recipe, Favorite, AIDishSuggestion, Ingredient, RecipeIngredient
import json
import re


def set_language(request):
    lang_code = request.GET.get('lang')
    next_url = request.META.get('HTTP_REFERER', '/')
    if lang_code and lang_code in [l[0] for l in settings.LANGUAGES]:
        translation.activate(lang_code)
        request.session['django_language'] = lang_code
    return redirect(next_url)

DISH_ICONS = ['🍲', '🥘', '🍳', '🥗', '🌮', '🍕', '🥙']
DISH_ACCENTS = ['#ff6b35', '#8b5cf6', '#10b981', '#f59e0b', "#ea2587", '#06b6d4', '#ef4444']


def serialize_dish_card(dish):
    return {
        'id': dish.id,
        'title': dish.title,
        'summary': dish.summary,
        'cooking_time': dish.cooking_time,
        'difficulty': dish.get_difficulty_display(),
        'url': f'/dish/{dish.id}/',
        'icon': DISH_ICONS[dish.id % len(DISH_ICONS)],
        'accent': DISH_ACCENTS[dish.id % len(DISH_ACCENTS)],
    }

client = Groq(api_key="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")

# ----------------------------------------------------------------------

def home(request):
    return render(request, 'home.html')

# -----------------------------------------------------------------------------

def _save_ai_dishes(user, ingredients_str, ai_text, ai_request=None):
    dishes_data = parse_ai_dishes(ai_text)
    dishes = []
    for dish in dishes_data:
        dishes.append(AIDishSuggestion.objects.create(
            ai_request=ai_request,
            user=user,
            title=dish['title'],
            summary=dish['summary'],
            instructions=dish['instructions'],
            ingredients_text=dish['ingredients_text'] or ingredients_str,
            cooking_time=dish['cooking_time'],
            difficulty=dish['difficulty'],
        ))
    return dishes


def _call_ai_for_dishes(ingredients_str):
    prompt = build_multi_dish_prompt(ingredients_str)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


@login_required
def recipe_search(request):
    dishes = None
    ingredients_list = None
    error = None

    if request.method == "POST":
        ingredients = request.POST.get("ingredients", "").strip()

        if ingredients:
            try:
                ai_text = _call_ai_for_dishes(ingredients)
                ai_request = AIRecipeRequest.objects.create(
                    user=request.user,
                    ingredients_text=ingredients,
                    detected_ingredients=ingredients,
                    ai_response=ai_text,
                )
                dishes = _save_ai_dishes(
                    request.user,
                    ingredients,
                    ai_text,
                    ai_request=ai_request,
                )
                ingredients_list = [i.strip() for i in ingredients.split(",") if i.strip()]
            except Exception as e:
                error = f"Не удалось получить варианты блюд: {e}"

    return render(request, "recipe_search.html", {
        "dishes": dishes,
        "dishes_json": [serialize_dish_card(d) for d in dishes] if dishes else None,
        "ingredients_list": ingredients_list,
        "ingredients_json": ingredients_list,
        "error": error,
    })

# ---------------------------------------------------------------------------------------------------

import json

@login_required
def image_search(request):
    dishes = None
    result = None
    error = None
    detected_ingredients_json = None

    if request.method == "POST":
        manual_ingredients = request.POST.get("manual_ingredients")
        image = request.FILES.get("image")

        # Case 1: User submitted manual ingredients to get recipes
        if manual_ingredients:
            try:
                ingredients_data = json.loads(manual_ingredients)
                if ingredients_data:
                    ingredients_str = ", ".join(ingredients_data)
                    ai_text = _call_ai_for_dishes(ingredients_str)
                    ai_request = AIRecipeRequest.objects.create(
                        user=request.user,
                        ingredients_text=ingredients_str,
                        detected_ingredients=ingredients_str,
                        ai_response=ai_text,
                    )
                    dishes = _save_ai_dishes(
                        request.user,
                        ingredients_str,
                        ai_text,
                        ai_request=ai_request,
                    )
                    result = ai_request
            except Exception as e:
                error = f"Произошла ошибка: {str(e)}"
        # Case 2: User uploaded image to detect ingredients
        elif image:
            try:
                obj = AIRecipeRequest.objects.create(
                    user=request.user,
                    image=image,
                    detected_ingredients="",
                    ai_response=""
                )

                products = detect_products(obj.image.path)

                if not products:
                    products = []  # Empty list so user can add their own

                obj.detected_ingredients = ", ".join(products)
                obj.save()
                result = obj
                detected_ingredients_json = products
            except Exception as e:
                error = f"Произошла ошибка при анализе: {str(e)}"
        else:
            error = "Пожалуйста, загрузите фото или добавьте ингредиенты."

    return render(request, 'image_search.html', {
        'result': result,
        'dishes': dishes,
        'detected_ingredients_json': (
            detected_ingredients_json or
            ([i.strip() for i in result.detected_ingredients.split(',') if i.strip()]
             if result and result.detected_ingredients else None)
        ),
        'error': error,
    })

# --------------------------------------------------------------------------------------------

@login_required
def ai_dish_detail(request, dish_id):
    dish = get_object_or_404(
        AIDishSuggestion.objects.select_related('ai_request', 'saved_recipe'),
        id=dish_id,
        user=request.user,
    )
    ingredients = [i.strip() for i in dish.ingredients_text.split(",") if i.strip()]
    if not ingredients and dish.ingredients_text:
        ingredients = [dish.ingredients_text]
    video_links = dish.get_video_links()

    return render(request, 'ai_dish_detail.html', {
        'dish': dish,
        'ingredients': ingredients,
        'ingredients_json': ingredients,
        'video_links': video_links,
        'dish_detail_json': {
            'title': dish.title,
            'summary': dish.summary,
            'instructions': dish.instructions,
            'cooking_time': dish.cooking_time,
            'difficulty': dish.get_difficulty_display(),
        },
    })


@login_required
def add_ai_favorite(request, dish_id):
    dish = get_object_or_404(AIDishSuggestion, id=dish_id, user=request.user)

    if dish.saved_recipe_id:
        return redirect('favorites')

    recipe = Recipe.objects.create(
        title=dish.title,
        description=dish.summary,
        instructions=dish.instructions,
        cooking_time=dish.cooking_time,
        servings=2,
        difficulty=dish.difficulty,
        created_by=request.user,
    )

    for name in [i.strip() for i in dish.ingredients_text.split(",") if i.strip()]:
        ingredient, _ = Ingredient.objects.get_or_create(name=name[:100])
        RecipeIngredient.objects.create(recipe=recipe,ingredient=ingredient,quantity="по вкусу",)

    Favorite.objects.get_or_create(user=request.user, recipe=recipe)
    dish.saved_recipe = recipe
    dish.save(update_fields=['saved_recipe'])

    return redirect('favorites')

# --------------------------------------------------------------------------------------------

@login_required
def favorites(request):
    favorites = Favorite.objects.filter(
        user=request.user
    ).select_related('recipe').prefetch_related('recipe__ai_suggestions')
    
    return render(request, 'favorites.html', {'favorites': favorites})

@login_required
def add_favorite(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    Favorite.objects.get_or_create(user=request.user,recipe=recipe)
    return redirect('favorites')

@login_required
def remove_favorite(request, recipe_id):
    Favorite.objects.filter(user=request.user,recipe_id=recipe_id).delete()
    return redirect('favorites')

# --------------------------------------------------------------------

@login_required
def history(request):
    items = AIRecipeRequest.objects.filter(
        user=request.user
    ).prefetch_related('dishes').order_by('-created_at')

    return render(request, "history.html", {
        "items": items
    })


@login_required
def clear_history(request):
    if request.method == "POST":
        # Delete all user's history
        AIRecipeRequest.objects.filter(user=request.user).delete()
    return redirect('history')

# ------------------------------------------------------------------------------------------------

@login_required
def profile(request):
    history_count = AIRecipeRequest.objects.filter(user=request.user).count()
    favorites_count = Favorite.objects.filter(user=request.user).count()
    context = {
        'history_count': history_count,
        'favorites_count': favorites_count
    }
    return render(request, 'profile.html', context)


# ===== WEEKLY MEAL PLANNER FUNCTIONS =====

def _build_weekly_meal_prompt(goal, meals_per_day, favorite_foods, forbidden_foods, allergies, max_cooking_time, budget):
    """Build prompt for AI to generate a weekly meal plan."""
    
    budget_description = {
        'low': 'Use cheap and accessible ingredients',
        'medium': 'Use moderately priced ingredients',
        'high': 'Use premium and high-quality ingredients'
    }.get(budget, 'Use moderately priced ingredients')
    
    goal_description = {
        'weight_loss': 'Low calorie, high protein, balanced macros for weight loss',
        'muscle_gain': 'High calorie, high protein, suitable for muscle building',
        'maintain': 'Balanced calories and macros for maintenance'
    }.get(goal, 'Balanced macros for maintenance')
    
    favorite_section = f"Prefer these foods: {favorite_foods}" if favorite_foods else ""
    forbidden_section = f"Never use: {forbidden_foods}" if forbidden_foods else ""
    allergies_section = f"User has allergies to: {allergies}" if allergies else ""

    prompt = f"""Ты — ПРОФЕССИОНАЛЬНЫЙ персональный тренер и диетолог.

ЗАДАЧА: Создай идеальный недельный план питания (7 дней).

🎯 ТРЕБОВАНИЯ:
- Цель: {goal_description}
- Приёмов пищи в день: {meals_per_day} (Breakfast, Lunch, Dinner, Snack if applicable)
- Максимальное время приготовления: {max_cooking_time} минут
- Бюджет: {budget_description}
{favorite_section}
{forbidden_section}
{allergies_section}

📋 ДЛЯ КАЖДОГО БЛЮДА УКАЖИ:
- title: Название блюда
- description: Краткое описание (1-2 предложения)
- ingredients: Список ингредиентов с количеством (через запятую)
- instructions: Пошаговые инструкции приготовления
- cooking_time: Время приготовления в минутах (не более {max_cooking_time})
- calories: Калории на порцию
- protein: Белки в граммах
- fat: Жиры в граммах
- carbs: Углеводы в граммах

📅 ФОРМАТ ОТВЕТА — ТОЛЬКО валидный JSON (без markdown, без ``` блоков):
{{
  "plan": [
    {{
      "day": 1,
      "day_name": "Monday",
      "meals": [
        {{
          "meal_type": "breakfast",
          "title": "...",
          "description": "...",
          "ingredients": "...",
          "instructions": "...",
          "cooking_time": 15,
          "calories": 300,
          "protein": 20,
          "fat": 10,
          "carbs": 30
        }}
      ]
    }}
  ]
}}

⚠️ КРИТИЧЕСКИЕ ПРАВИЛА:
- JSON должен быть ВАЛИДНЫМ и парсируемым
- 7 дней в плане, каждый день имеет нужное количество приёмов
- Все значения калорий, белков, жиров, углеводов — числа
- Время приготовления не превышает {max_cooking_time} минут
"""
    
    return prompt


def _parse_weekly_meal_plan(ai_text):
    """Parse AI response into structured meal plan data."""
    text = ai_text.strip()
    
    # Try to extract JSON from markdown fences first
    fence_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    
    # Find JSON boundaries
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end + 1]
    
    data = json.loads(text)
    plan = data.get('plan', [])
    
    if not isinstance(plan, list) or not plan:
        raise ValueError('AI did not return a valid meal plan')
    
    return plan


def _save_weekly_meal_plan(user, meal_plan_obj, plan_data):
    """Save weekly meal plan and daily meals to database."""
    from .models import WeeklyMealPlan, DailyMeal
    
    for day_data in plan_data:
        day_num = day_data.get('day', 1) - 1  # Convert to 0-indexed
        meals = day_data.get('meals', [])
        
        for meal_data in meals:
            meal_type = meal_data.get('meal_type', 'breakfast')
            
            DailyMeal.objects.create(
                weekly_plan=meal_plan_obj,
                day_of_week=day_num,
                meal_type=meal_type,
                title=meal_data.get('title', 'Unnamed Meal'),
                description=meal_data.get('description', ''),
                ingredients=meal_data.get('ingredients', ''),
                cooking_time=int(meal_data.get('cooking_time', 30)),
                calories=int(meal_data.get('calories', 0)),
                protein=float(meal_data.get('protein', 0)),
                fat=float(meal_data.get('fat', 0)),
                carbs=float(meal_data.get('carbs', 0)),
            )


@login_required
def weekly_meal_planner(request):
    """Display weekly meal planner form and handle generation."""
    from .forms import WeeklyMealPlanForm
    from .models import WeeklyMealPlan, DailyMeal
    
    error = None
    meal_plan = None
    daily_meals_by_day = None
    
    if request.method == "POST":
        form = WeeklyMealPlanForm(request.POST)
        if form.is_valid():
            try:
                # Create meal plan object (without saving to DB yet)
                meal_plan_obj = form.save(commit=False)
                meal_plan_obj.user = request.user
                
                # Build prompt for AI
                prompt = _build_weekly_meal_prompt(
                    goal=meal_plan_obj.goal,
                    meals_per_day=meal_plan_obj.meals_per_day,
                    favorite_foods=meal_plan_obj.favorite_foods,
                    forbidden_foods=meal_plan_obj.forbidden_foods,
                    allergies=meal_plan_obj.allergies,
                    max_cooking_time=meal_plan_obj.max_cooking_time,
                    budget=meal_plan_obj.budget,
                )
                
                # Call AI
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                )
                ai_response = response.choices[0].message.content
                
                # Parse response
                plan_data = _parse_weekly_meal_plan(ai_response)
                
                # Save to database
                meal_plan_obj.ai_response = ai_response
                meal_plan_obj.save()
                
                # Save daily meals
                _save_weekly_meal_plan(request.user, meal_plan_obj, plan_data)
                
                # Fetch saved meals for display
                meal_plan = meal_plan_obj
                daily_meals = DailyMeal.objects.filter(weekly_plan=meal_plan_obj).order_by('day_of_week', 'meal_type')
                
                # Group by day
                daily_meals_by_day = {}
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                for day_num in range(7):
                    daily_meals_by_day[day_num] = {
                        'day_name': days[day_num],
                        'meals': list(daily_meals.filter(day_of_week=day_num))
                    }
                
            except Exception as e:
                error = f"Error generating meal plan: {str(e)}"
                form = WeeklyMealPlanForm()
    else:
        form = WeeklyMealPlanForm()
    
    context = {
        'form': form,
        'meal_plan': meal_plan,
        'daily_meals_by_day': daily_meals_by_day,
        'error': error,
        'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        'meal_type_icons': {
            'breakfast': '🍳',
            'lunch': '🍽️',
            'dinner': '🍲',
            'snack': '🥗',
        }
    }
    
    return render(request, 'weekly_meal_planner.html', context)


@login_required
def meal_plans_history(request):
    """Display user's meal plan history (including soft-deleted plans)."""
    from .models import WeeklyMealPlan
    
    # Show all plans (active and soft-deleted), sorted by creation date
    plans = WeeklyMealPlan.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'plans': plans,
    }
    
    return render(request, 'meal_plans_history.html', context)


@login_required
def meal_plan_detail(request, plan_id):
    """Display details of a specific meal plan."""
    from .models import WeeklyMealPlan, DailyMeal
    
    meal_plan = get_object_or_404(WeeklyMealPlan, id=plan_id, user=request.user)
    daily_meals = DailyMeal.objects.filter(weekly_plan=meal_plan).order_by('day_of_week', 'meal_type')
    
    # Group by day
    daily_meals_by_day = {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day_num in range(7):
        daily_meals_by_day[day_num] = {
            'day_name': days[day_num],
            'meals': list(daily_meals.filter(day_of_week=day_num))
        }
    
    context = {
        'meal_plan': meal_plan,
        'daily_meals_by_day': daily_meals_by_day,
        'days': days,
        'meal_type_icons': {
            'breakfast': '🍳',
            'lunch': '🍽️',
            'dinner': '🍲',
            'snack': '🥗',
        }
    }
    
    return render(request, 'meal_plan_detail.html', context)


@login_required
def delete_meal_plan(request, plan_id):
    """Soft delete a meal plan (mark as deleted but keep in history)."""
    from django.utils import timezone
    from .models import WeeklyMealPlan
    
    meal_plan = get_object_or_404(WeeklyMealPlan, id=plan_id, user=request.user)
    
    if request.method == "POST":
        # Soft delete: mark as deleted instead of removing
        meal_plan.is_deleted = True
        meal_plan.deleted_at = timezone.now()
        meal_plan.save()
        return redirect('meal_plans_history')
    
    context = {
        'meal_plan': meal_plan,
    }
    
    return render(request, 'confirm_delete_meal_plan.html', context)


@login_required
def meal_plan_permanent_delete(request, plan_id):
    """Permanently delete a meal plan (remove from database)."""
    from .models import WeeklyMealPlan
    
    meal_plan = get_object_or_404(WeeklyMealPlan, id=plan_id, user=request.user)
    
    if request.method == "POST":
        # Hard delete: permanently remove from database
        meal_plan.delete()
        return redirect('meal_plans_history')
    
    return redirect('meal_plans_history')


@login_required
def regenerate_meal_plan(request, plan_id):
    """Regenerate a meal plan with the same parameters."""
    from .models import WeeklyMealPlan, DailyMeal
    
    original_plan = get_object_or_404(WeeklyMealPlan, id=plan_id, user=request.user)
    
    # Prevent regenerating deleted plans
    if original_plan.is_deleted:
        return redirect('meal_plans_history')
    
    if request.method == "POST":
        try:
            # Build new prompt with same parameters
            prompt = _build_weekly_meal_prompt(
                goal=original_plan.goal,
                meals_per_day=original_plan.meals_per_day,
                favorite_foods=original_plan.favorite_foods,
                forbidden_foods=original_plan.forbidden_foods,
                allergies=original_plan.allergies,
                max_cooking_time=original_plan.max_cooking_time,
                budget=original_plan.budget,
            )
            
            # Call AI
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
            )
            ai_response = response.choices[0].message.content
            
            # Parse response
            plan_data = _parse_weekly_meal_plan(ai_response)
            
            # Create new meal plan
            new_plan = WeeklyMealPlan.objects.create(
                user=request.user,
                goal=original_plan.goal,
                meals_per_day=original_plan.meals_per_day,
                favorite_foods=original_plan.favorite_foods,
                forbidden_foods=original_plan.forbidden_foods,
                allergies=original_plan.allergies,
                max_cooking_time=original_plan.max_cooking_time,
                budget=original_plan.budget,
                ai_response=ai_response,
            )
            
            # Save daily meals
            _save_weekly_meal_plan(request.user, new_plan, plan_data)
            
            return redirect('meal_plan_detail', plan_id=new_plan.id)
            
        except Exception as e:
            error = f"Error regenerating meal plan: {str(e)}"
            context = {
                'meal_plan': original_plan,
                'error': error,
            }
            return render(request, 'meal_plan_detail.html', context)
    
    return redirect('meal_plan_detail', plan_id=plan_id)
