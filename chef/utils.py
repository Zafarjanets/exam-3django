import json
import re
from urllib.parse import quote_plus

_model = None


def _get_yolo_model():
    global _model
    if _model is None:
        from ultralytics import YOLO
        _model = YOLO("yolov8n.pt")
    return _model

MULTI_DISH_PROMPT = """
Ты — СТРОГИЙ кулинарный AI.

❗ КРИТИЧЕСКИЕ ПРАВИЛА:
- Используй ТОЛЬКО входные ингредиенты
- НИКОГДА не добавляй новые продукты
- НЕ исправляй слова пользователя (писать как есть)
- НЕ добавляй "яйца, молоко, масло" если их нет во входе
- Предложи ровно 3 разных варианта блюд

ИНГРЕДИЕНТЫ (как есть):
{ingredients}

❗ ЗАДАЧА:
Придумай 3 разных блюда только из этих продуктов.

❗ ФОРМАТ ОТВЕТА — ТОЛЬКО валидный JSON без markdown:
{{
  "dishes": [
    {{
      "title": "Название блюда",
      "summary": "Краткое описание в 1-2-3 предложения",
      "ingredients": "список ингредиентов с количеством",
      "instructions": "Пошаговая инструкция приготовления",
      "cooking_time": 20,
      "difficulty": "easy"
    }}
  ]
}}

difficulty: только "easy", "medium" или "hard".
"""


def build_multi_dish_prompt(ingredients):
    return MULTI_DISH_PROMPT.format(ingredients=ingredients)


def parse_ai_dishes(ai_text):
    text = ai_text.strip()
    fence_match = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        text = text[start:end + 1]

    data = json.loads(text)
    dishes = data.get('dishes', [])
    if not isinstance(dishes, list) or not dishes:
        raise ValueError('AI не вернул список блюд')

    parsed = []
    for dish in dishes[:3]:
        difficulty = dish.get('difficulty', 'easy')
        if difficulty not in ('easy', 'medium', 'hard'):
            difficulty = 'easy'
        parsed.append({
            'title': dish.get('title', 'Блюдо без названия').strip(),
            'summary': dish.get('summary', '').strip(),
            'ingredients_text': dish.get('ingredients', '').strip(),
            'instructions': dish.get('instructions', '').strip(),
            'cooking_time': max(int(dish.get('cooking_time', 30) or 30), 1),
            'difficulty': difficulty,
        })
    return parsed


def build_cooking_video_links(title, ingredients_text=''):
    ingredients = [i.strip() for i in ingredients_text.split(',') if i.strip()]
    ing_short = ', '.join(ingredients[:4])

    links = [
        {
            'label': f'Как приготовить «{title}»',
            'url': (
                'https://www.youtube.com/results?search_query='
                + quote_plus(f'{title} рецепт приготовление')
            ),
        },
    ]

    if ing_short:
        links.append({
            'label': f'«{title}» из продуктов: {ing_short}',
            'url': (
                'https://www.youtube.com/results?search_query='
                + quote_plus(f'{title} {ing_short} рецепт')
            ),
        })
        links.append({
            'label': f'Рецепты из: {ing_short}',
            'url': (
                'https://www.youtube.com/results?search_query='
                + quote_plus(f'{ing_short} рецепт')
            ),
        })

    return links


def detect_products(image_path):
    model = _get_yolo_model()
    results = model(image_path)

    names = []
    print(results)

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            name = model.names[cls_id]
            names.append(name)

    return list(set(names))