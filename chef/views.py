from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from groq import Groq
from .utils import detect_products
from .models import AIRecipeRequest, Recipe, Favorite

# Initialize Groq Client
client = Groq(api_key="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")

# ----------------------------------------------------------------------

def home(request):
    return render(request, 'home.html')

# -----------------------------------------------------------------------------

@login_required
def recipe_search(request):
    result = None
    if request.method == "POST":
        ingredients = request.POST.get("ingredients")

        if ingredients:
            prompt = f"""
Ты — СТРОГИЙ кулинарный AI.

❗ КРИТИЧЕСКИЕ ПРАВИЛА:
- Используй ТОЛЬКО входные ингредиенты
- НИКОГДА не добавляй новые продукты
- НЕ исправляй слова пользователя (писать как есть)
- НЕ добавляй “яйца, молоко, масло” если их нет во входе
- НЕ улучшай текст пользователя

ИНГРЕДИЕНТЫ (как есть):
{ingredients}

❗ ЗАДАЧА:
Создай реальный рецепт только из этих продуктов.

❗ ЕСЛИ МАЛО ПРОДУКТОВ:
придумай простое блюдо, но используй только их

ФОРМАТ:

Название блюда:
...

Ингредиенты:
(только входные, без изменений)

Шаги:
1.
2.
3.
4.

Время:
Сложность:
"""
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            ai_text = response.choices[0].message.content

            result = {
                "ingredients": [i.strip() for i in ingredients.split(",")],
                "recipe": ai_text
            }

    return render(request, "recipe_search.html", {"result": result})

# ---------------------------------------------------------------------------------------------------

@login_required
def image_search(request):
    result = None
    error = None
    if request.method == "POST":
        image = request.FILES.get("image")
        if not image:
            error = "Пожалуйста, выберите фото продуктов."
        else:
            try:
                # 1. Create request record in DB
                obj = AIRecipeRequest.objects.create(
                    user=request.user,
                    image=image,
                    detected_ingredients="",
                    ai_response=""
                )

                # 2. Run YOLO product detection
                products = detect_products(obj.image.path)

                if not products:
                    error = "Не удалось распознать продукты на фото. Пожалуйста, попробуйте другое изображение."
                    obj.delete()
                else:
                    ingredients_str = ", ".join(products)

                    # 3. Call Groq to generate recipe from detected ingredients
                    prompt = f"""
Ты — СТРОГИЙ кулинарный AI.

❗ КРИТИЧЕСКИЕ ПРАВИЛА:
- Используй ТОЛЬКО входные ингредиенты
- НИКОГДА не добавляй новые продукты
- НЕ исправляй слова пользователя (писать как есть)
- НЕ добавляй “яйца, молоко, масло” если их нет во входе
- НЕ улучшай текст пользователя

ИНГРЕДИЕНТЫ (обнаруженные на фото):
{ingredients_str}

❗ ЗАДАЧА:
Создай реальный рецепт только из этих продуктов.

ФОРМАТ:
Название блюда:
...

Ингредиенты:
...

Шаги:
1.
...

Время:
Сложность:
"""
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    ai_text = response.choices[0].message.content

                    # 4. Save results to DB
                    obj.detected_ingredients = ingredients_str
                    obj.ai_response = ai_text
                    obj.save()

                    result = obj
            except Exception as e:
                error = f"Произошла ошибка при анализе: {str(e)}"

    return render(request, 'image_search.html', {'result': result, 'error': error})

# --------------------------------------------------------------------------------------------

@login_required
def favorites(request):
    favorites = Favorite.objects.filter(
        user=request.user
    ).select_related('recipe')

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
    ).order_by('-created_at')

    return render(request, "history.html", {
        "items": items
    })

# ------------------------------------------------------------------------------------------------

@login_required
def profile(request):
    # Retrieve some stats to display on profile
    history_count = AIRecipeRequest.objects.filter(user=request.user).count()
    favorites_count = Favorite.objects.filter(user=request.user).count()
    context = {
        'history_count': history_count,
        'favorites_count': favorites_count
    }
    return render(request, 'profile.html', context)