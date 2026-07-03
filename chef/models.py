from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    DIFFICULTY_CHOICES = [('easy', 'Easy'),('medium', 'Medium'),('hard', 'Hard'),]
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructions = models.TextField()
    cooking_time = models.PositiveIntegerField(help_text='Cooking time in minutes')
    servings = models.PositiveIntegerField(default=1)
    difficulty = models.CharField(max_length=10,choices=DIFFICULTY_CHOICES,default='easy')
    image = models.ImageField(upload_to='recipes/',blank=True,null=True)
    ingredients = models.ManyToManyField(Ingredient,through='RecipeIngredient',related_name='recipes')
    created_by = models.ForeignKey( settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='recipes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe,on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient,on_delete=models.CASCADE)
    quantity = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.ingredient.name} ({self.quantity})'


class Favorite(models.Model):
    user = models.ForeignKey( settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'recipe')
        
    def __str__(self):
        return f'{self.user.username} - {self.recipe.title}'


class AIRecipeRequest(models.Model):
    user = models.ForeignKey( settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    ingredients_text = models.TextField(blank=True,null=True,help_text='Products entered by user')
    image = models.ImageField(upload_to='ingredient_images/',blank=True,null=True)
    detected_ingredients = models.TextField(blank=True,null=True)
    ai_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'AI Request #{self.id}'


class AIDishSuggestion(models.Model):
    ai_request = models.ForeignKey(
        AIRecipeRequest,
        on_delete=models.CASCADE,
        related_name='dishes',
        null=True,
        blank=True,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    summary = models.TextField()
    instructions = models.TextField()
    ingredients_text = models.TextField(blank=True)
    cooking_time = models.PositiveIntegerField(default=30)
    difficulty = models.CharField(
        max_length=10,
        choices=Recipe.DIFFICULTY_CHOICES,
        default='easy',
    )
    saved_recipe = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_suggestions',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    @property
    def is_favorited(self):
        return self.saved_recipe_id is not None

    def get_video_links(self):
        from .utils import build_cooking_video_links
        return build_cooking_video_links(self.title, self.ingredients_text)

    @property
    def photo_url(self):
        """Get a relevant food photo URL based on the dish title."""
        import urllib.parse
        search_term = urllib.parse.quote(self.title)
        # Use Unsplash source for random food photos based on search term
        return f"https://source.unsplash.com/600x400/?{search_term},food,cooking"

class Review(models.Model):
    user = models.ForeignKey( settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,on_delete=models.CASCADE,related_name='reviews')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.recipe.title}'


class WeeklyMealPlan(models.Model):
    GOAL_CHOICES = [
        ('weight_loss', 'Снижение Веса'),
        ('muscle_gain', 'Набор Мышц'),
        ('maintain', 'Поддержание Веса'),
    ]
    BUDGET_CHOICES = [
        ('low', 'Низкий 💰'),
        ('medium', 'Средний 💵'),
        ('high', 'Высокий 💎'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='weekly_meal_plans')
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    meals_per_day = models.IntegerField(default=3)  # 3-6 meals
    favorite_foods = models.TextField(blank=True, null=True)
    forbidden_foods = models.TextField(blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    max_cooking_time = models.IntegerField(default=60)  # in minutes
    budget = models.CharField(max_length=10, choices=BUDGET_CHOICES, default='medium')
    ai_response = models.TextField(blank=True, null=True)  # Store raw AI response
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)  # Soft delete flag
    deleted_at = models.DateTimeField(blank=True, null=True)  # Soft delete timestamp

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Weekly Plan #{self.id} - {self.user.username}'


class DailyMeal(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]

    weekly_plan = models.ForeignKey(WeeklyMealPlan, on_delete=models.CASCADE, related_name='daily_meals')
    day_of_week = models.IntegerField(default=0)  # 0=Monday, 6=Sunday
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    ingredients = models.TextField()
    cooking_time = models.IntegerField(default=30)  # in minutes
    calories = models.IntegerField(default=0)
    protein = models.FloatField(default=0)  # grams
    fat = models.FloatField(default=0)  # grams
    carbs = models.FloatField(default=0)  # grams

    class Meta:
        ordering = ['day_of_week', 'meal_type']

    def __str__(self):
        return f'{self.title} - Day {self.day_of_week + 1}'


class WorkoutPlan(models.Model):
    """Workout plan automatically generated for each meal plan."""
    INTENSITY_CHOICES = [
        ('low', 'Низкая 🟢'),
        ('medium', 'Средняя 🟡'),
        ('high', 'Высокая 🔴'),
    ]
    
    meal_plan = models.OneToOneField(WeeklyMealPlan, on_delete=models.CASCADE, related_name='workout_plan')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workout_plans')
    goal = models.CharField(max_length=20)  # weight_loss, muscle_gain, maintain
    intensity = models.CharField(max_length=10, choices=INTENSITY_CHOICES, default='medium')
    ai_response = models.TextField(blank=True, null=True)  # Store raw AI response
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Workout Plan #{self.id} - {self.meal_plan.get_goal_display()}'
    
    def get_workout_badge(self):
        """Get emoji badge based on goal."""
        badges = {
            'weight_loss': '🔥 Сжигание Жира',
            'muscle_gain': '💪 Набор Мышц',
            'maintain': '⚖️ Поддержание',
        }
        return badges.get(self.goal, '🏋️ Тренировка')


class WorkoutDay(models.Model):
    """Individual day in a 7-day workout plan."""
    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='workout_days')
    day_of_week = models.IntegerField(default=0)  # 0=Monday, 6=Sunday
    rest_day = models.BooleanField(default=False)  # True if it's a rest day
    focus = models.CharField(max_length=100, blank=True)  # e.g., "Upper Body", "Cardio Day"
    duration = models.IntegerField(default=45)  # in minutes
    difficulty = models.CharField(max_length=10, choices=WorkoutPlan.INTENSITY_CHOICES, default='medium')
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['day_of_week']
    
    def __str__(self):
        return f'Day {self.day_of_week + 1} - {self.focus if self.focus else "Rest Day"}'
    
    def get_day_name(self):
        """Get day name in Russian."""
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        return days[self.day_of_week]


class Exercise(models.Model):
    """Individual exercise within a workout day."""
    EXERCISE_TYPES = [
        ('push_ups', 'Отжимания'),
        ('pull_ups', 'Подтягивания'),
        ('squats', 'Приседания'),
        ('plank', 'Планка'),
        ('cardio', 'Кардио'),
        ('running', 'Бег'),
        ('abs', 'Пресс'),
        ('lunges', 'Выпады'),
        ('burpees', 'Берпи'),
        ('jumping', 'Прыжки'),
        ('stretching', 'Растяжка'),
        ('other', 'Другое'),
    ]
    
    workout_day = models.ForeignKey(WorkoutDay, on_delete=models.CASCADE, related_name='exercises')
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPES)
    name = models.CharField(max_length=200)  # Custom name
    reps_or_duration = models.CharField(max_length=100)  # e.g., "3x10" or "30 seconds"
    difficulty = models.CharField(max_length=10, choices=WorkoutPlan.INTENSITY_CHOICES, default='medium')
    description = models.TextField(blank=True)  # Tips/instructions
    order = models.PositiveIntegerField(default=0)  # Order within the day
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f'{self.name} - {self.reps_or_duration}'
    
    def get_exercise_emoji(self):
        """Get emoji for exercise type."""
        emojis = {
            'push_ups': '💪',
            'pull_ups': '🤸',
            'squats': '🦵',
            'plank': '📏',
            'cardio': '🏃',
            'running': '🏃‍♂️',
            'abs': '🫀',
            'lunges': '🚶',
            'burpees': '⚡',
            'jumping': '🤾',
            'stretching': '🧘',
            'other': '🏋️',
        }
        return emojis.get(self.exercise_type, '🏋️')