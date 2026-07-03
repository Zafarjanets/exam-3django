from django import forms
from .models import WeeklyMealPlan


class WeeklyMealPlanForm(forms.ModelForm):
    favorite_foods = forms.CharField(
        label='Favorite Foods',
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your favorite foods (comma-separated)',
            'rows': 2,
        }),
        required=False
    )
    forbidden_foods = forms.CharField(
        label='Forbidden Foods',
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Foods you cannot eat (comma-separated)',
            'rows': 2,
        }),
        required=False
    )
    allergies = forms.CharField(
        label='Allergies',
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'placeholder': 'Your allergies (comma-separated)',
            'rows': 2,
        }),
        required=False
    )

    class Meta:
        model = WeeklyMealPlan
        fields = ['goal', 'meals_per_day', 'favorite_foods', 'forbidden_foods', 'allergies', 'max_cooking_time', 'budget']
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
            }),
            'budget': forms.Select(attrs={
                'class': 'form-input',
            }),
        }
