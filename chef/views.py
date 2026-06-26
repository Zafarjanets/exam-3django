from django.shortcuts import render,redirect,get_object_or_404
from groq import Groq
from .utils import detect_products
from .models import AIRecipeRequest
from .utils import detect_products
from .models import Recipe, Favorite



# ----------------------------------------------------------------------

def home(request):
    return render(request, 'home.html')

# -----------------------------------------------------------------------------
client = Groq(api_key="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")
def recipe_search(request):
    result = None

    if request.method == "POST":
        ingredients = request.POST.get("ingredients")

        print("INPUT:", ingredients)

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
def image_search(request):
    return render(request, 'image_search.html')


def upload_photo(request):
    if request.method == "POST":
        image = request.FILES.get("image")
        

        obj = AIRecipeRequest.objects.create(
            user=request.user if request.user.is_authenticated else None,
            image=image,
            ai_response=""
        )

        products = detect_products(obj.image.path)

        obj.detected_ingredients = ",".join(products)
        obj.save()
        print(request.POST)
        print(request.FILES)
        return render(request, "result.html", {
            "products": products
        })
        

    return render(request, "upload.html")
# --------------------------------------------------------------------------------------------
def favorites(request):
    return render(request, 'favorites.html')

def add_favorite(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    Favorite.objects.get_or_create(
        user=request.user,
        recipe=recipe
    )

    return redirect('favorites')

def remove_favorite(request, recipe_id):
    Favorite.objects.filter(
        user=request.user,
        recipe_id=recipe_id
    ).delete()

    return redirect('favorites')

def favorites(request):
    favorites = Favorite.objects.filter(
        user=request.user
    ).select_related('recipe')

    return render(request, 'favorites.html', {
        'favorites': favorites
    })
# --------------------------------------------------------------------

def history(request):
    items = AIRecipeRequest.objects.all().order_by('-created_at')

    return render(request, "history.html", {"items": items})
def history(request):
    items = AIRecipeRequest.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(request, "history.html", {
        "items": items
    })
    
# ------------------------------------------------------------------------------------------------
def profile(request):
    return render(request, 'profile.html')