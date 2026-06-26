from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('search/', views.recipe_search, name='recipe_search'),
    path('image/', views.image_search, name='image_search'),
    path('favorites/', views.favorites, name='favorites'),
    path('favorite/add/<int:recipe_id>/', views.add_favorite, name='add_favorite'),
    path('favorite/remove/<int:recipe_id>/', views.remove_favorite, name='remove_favorite'),
    path('history/', views.history, name='history'),
    path('profile/', views.profile, name='profile'),
]