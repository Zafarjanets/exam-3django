import base64
from groq import Groq

client = Groq(api_key="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")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

try:
    image_path = "recipes/657007403d5cc46686.webp"
    base64_image = encode_image(image_path)
    
    prompt = """
Ты — профессиональный шеф-повар и кулинарный AI.
Изучи изображение и определи, какие продукты или ингредиенты на нем находятся.

Затем составь максимально подробный список возможных вариантов блюд и рецептов, которые можно приготовить с использованием этих продуктов. Предложи как можно больше разнообразных вариантов (от простых закусок до основных блюд).

Ответь СТРОГО в следующем формате:

Обнаруженные продукты:
[Перечисли здесь все распознанные продукты через запятую на русском языке, например: картофель, курица, сыр]

Варианты приготовления:
[Здесь распиши подробно и красиво рецепты и варианты блюд, которые можно приготовить с этим продуктом. Сделай структуру удобной с использованием Markdown]
"""
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/webp;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        model="meta-llama/llama-4-scout-17b-16e-instruct",
    )
    
    content = chat_completion.choices[0].message.content
    with open("scratch/output.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("Saved to scratch/output.txt successfully!")
except Exception as e:
    print("Error:", e)
