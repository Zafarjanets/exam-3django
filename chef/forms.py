from django import forms
from .models import WeeklyMealPlan


class WeeklyMealPlanForm(forms.ModelForm):
    favorite_foods = forms.CharField(
        label='Избранные Продукты',
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Укажите любимые продукты (через запятую)',
            'rows': 2,
        }),
        required=False
    )
    forbidden_foods = forms.CharField(
        label='Запрещенные Продукты',
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Продукты, которые вы не едите (через запятую)',
            'rows': 2,
        }),
        required=False
    )
    allergies = forms.CharField(
        label='Аллергии',
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Ваши аллергии (через запятую)',
            'rows': 2,
        }),
        required=False
    )

    class Meta:
        model = WeeklyMealPlan
        fields = ['goal', 'meals_per_day', 'favorite_foods', 'forbidden_foods', 'allergies', 'max_cooking_time', 'budget']
        labels = {
            'goal': 'Цель',
            'meals_per_day': 'Приемов в день',
            'max_cooking_time': 'Макс. время готовки',
            'budget': 'Бюджет',
        }
        widgets = {
            'goal': forms.Select(attrs={
                'class': 'form-input',
            }),
            'meals_per_day': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 3,
                'max': 6,
            }),
            'max_cooking_time': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 5,
                'max': 120,
                'placeholder': 'мин',
            }),
            'budget': forms.Select(attrs={
                'class': 'form-input',
            }),
        }
