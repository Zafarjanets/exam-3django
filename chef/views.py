from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from groq import Groq
from .utils import detect_products, build_multi_dish_prompt, parse_ai_dishes
from .models import AIRecipeRequest, Recipe, Favorite, AIDishSuggestion, Ingredient, RecipeIngredient

DISH_ICONS = ['🍲', '🥘', '🍳', '🥗', '🌮', '🍕', '🥙']
DISH_ACCENTS = ['#ff6b35', '#8b5cf6', '#10b981', '#f59e0b', '#ec4899', '#06b6d4', '#ef4444']


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

# Initialize Groq Client
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

@login_required
def image_search(request):
    dishes = None
    result = None
    error = None

    if request.method == "POST":
        image = request.FILES.get("image")
        if not image:
            error = "Пожалуйста, выберите фото продуктов."
        else:
            try:
                obj = AIRecipeRequest.objects.create(
                    user=request.user,
                    image=image,
                    detected_ingredients="",
                    ai_response=""
                )

                products = detect_products(obj.image.path)

                if not products:
                    error = "Не удалось распознать продукты на фото. Пожалуйста, попробуйте другое изображение."
                    obj.delete()
                else:
                    ingredients_str = ", ".join(products)
                    ai_text = _call_ai_for_dishes(ingredients_str)

                    obj.detected_ingredients = ingredients_str
                    obj.ai_response = ai_text
                    obj.save()

                    dishes = _save_ai_dishes(
                        request.user,
                        ingredients_str,
                        ai_text,
                        ai_request=obj,
                    )
                    result = obj
            except Exception as e:
                error = f"Произошла ошибка при анализе: {str(e)}"

    return render(request, 'image_search.html', {
        'result': result,
        'dishes': dishes,
        'dishes_json': [serialize_dish_card(d) for d in dishes] if dishes else None,
        'detected_ingredients_json': (
            [i.strip() for i in result.detected_ingredients.split(',') if i.strip()]
            if result and result.detected_ingredients else None
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
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=ingredient,
            quantity="по вкусу",
        )

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

    return render(request, 'favorites.html', {
        'favorites': favorites
    })

@login_required
def add_favorite(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    Favorite.objects.get_or_create(
        user=request.user,
        recipe=recipe
    )

    return redirect('favorites')

@login_required
def remove_favorite(request, recipe_id):
    Favorite.objects.filter(
        user=request.user,
        recipe_id=recipe_id
    ).delete()

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
