from django.urls import path
from . import views


urlpatterns = [
    path("register/", views.register_view, name="register"),
    path('confirm/', views.confirm_email, name='confirm'),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    ]