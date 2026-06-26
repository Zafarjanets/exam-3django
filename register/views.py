from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings
from random import randint

from .models import EmailConfirm


def send_email_confirmation(user):
    code = randint(100000, 999999)

    EmailConfirm.objects.update_or_create(
        user=user,
        defaults={"code": str(code)}
    )

    send_mail(
        subject="Email confirmation",
        message=f"Hello {user.username}!\n\nYour confirmation code is: {code}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    
def register_view(request):
    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if not username or not email or not password1 or not password2:
            return render(request, "accounts/register.html", {"error": "Please fill in all fields."})
        if password1 != password2:
            return render(request, "accounts/register.html", {"error": "Passwords do not match."})
        if User.objects.filter(username=username).exists():
            return render(request, "accounts/register.html", { "error": "Username already exists."})
        if User.objects.filter(email=email).exists():
            return render(request, "accounts/register.html", {"error": "Email already exists."})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            is_active=False
        )

        send_email_confirmation(user)
        return render(request, "accounts/confirm.html", {"email": email})

    return render(request, "accounts/register.html")
    