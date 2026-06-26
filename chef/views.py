from django.shortcuts import render
from groq import Groq
from dotenv import OPENAI_API_KEY

# ----------------------------------------------------------------------

def home(request):
    return render(request, 'home.html')

# -----------------------------------------------------------------------------
client = Groq(api_key=OPENAI_API_KEY)
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

# --------------------------------------------------------------------------------------------
def favorites(request):
    return render(request, 'favorites.html')

def history(request):
    return render(request, 'history.html')

def profile(request):
    return render(request, 'profile.html')