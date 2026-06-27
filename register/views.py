from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings
from random import randint

from .models import EmailConfirm


def send_email_confirmation(user):
    code = randint(1000, 9999)

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
        print(request.method)

        send_email_confirmation(user)
        request.session['confirm_email'] = email  
        return redirect('confirm')
    
    return render(request, "accounts/register.html")

def confirm_email(request):
    if request.method == "POST":
        email = request.POST.get("email")

        code = (
            request.POST.get("c1", "") +
            request.POST.get("c2", "") +
            request.POST.get("c3", "") +
            request.POST.get("c4", "")
        ).strip()

        user = User.objects.filter(email=email).first()
        if not user:
            return render(request, "accounts/confirm.html", {"error": "Email not found."})
        confirm = EmailConfirm.objects.filter(user=user, code=code).first()
        if not confirm:
            return render(request, "accounts/confirm.html", {"email": email, "error": "Invalid confirmation code."})
        user.is_active = True
        user.save()
        login(request, user, backend='register.backends.EmailOrUsernameBackend')
        return redirect("home")
    email = request.session.get('confirm_email', '')
    return render(request, "accounts/confirm.html", {"email": email})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if not user:
            inactive = User.objects.filter(username=username, is_active=False).exists()
            if inactive:
                return redirect('confirm')

            return render(request, "accounts/login.html", {
                "error": "Invalid username or password."
            })

        login(request, user)
        return redirect("home")

    return render(request, "accounts/login.html")
    
def logout_view(request):
    logout(request)
    return redirect('login')

            
            