# Generated migration for WeeklyMealPlan and DailyMeal models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('chef', '0003_aidishsuggestion'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WeeklyMealPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('goal', models.CharField(choices=[('weight_loss', 'Weight Loss'), ('muscle_gain', 'Muscle Gain'), ('maintain', 'Maintain Weight')], max_length=20)),
                ('meals_per_day', models.IntegerField(default=3)),
                ('favorite_foods', models.TextField(blank=True, null=True)),
                ('forbidden_foods', models.TextField(blank=True, null=True)),
                ('allergies', models.TextField(blank=True, null=True)),
                ('max_cooking_time', models.IntegerField(default=60)),
                ('budget', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=10)),
                ('ai_response', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='weekly_meal_plans', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DailyMeal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.IntegerField(default=0)),
                ('meal_type', models.CharField(choices=[('breakfast', 'Breakfast'), ('lunch', 'Lunch'), ('dinner', 'Dinner'), ('snack', 'Snack')], max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('ingredients', models.TextField()),
                ('cooking_time', models.IntegerField(default=30)),
                ('calories', models.IntegerField(default=0)),
                ('protein', models.FloatField(default=0)),
                ('fat', models.FloatField(default=0)),
                ('carbs', models.FloatField(default=0)),
                ('weekly_plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_meals', to='chef.weeklymealplan')),
            ],
            options={
                'ordering': ['day_of_week', 'meal_type'],
            },
        ),
    ]
