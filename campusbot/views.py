from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

def auth_page(request):

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── LOGIN ──────────────────────────────
        if action == 'login':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'login_error:Invalid username or password')

        # ── SIGNUP ─────────────────────────────
        elif action == 'signup':
            username = request.POST.get('username')
            password = request.POST.get('password')
            confirm  = request.POST.get('confirm_password')

            if password != confirm:
                messages.error(request, 'signup_error:Passwords do not match')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'signup_error:Username already taken')
            elif len(password) < 6:
                messages.error(request, 'signup_error:Password must be at least 6 characters')
            else:
                User.objects.create_user(username=username, password=password)
                messages.success(request, 'signup_success:Account created! You can now log in.')

        # ── FORGOT PASSWORD ────────────────────
        elif action == 'forgot':
            username = request.POST.get('username')
            new_pass = request.POST.get('new_password')
            confirm  = request.POST.get('confirm_new_password')

            if not User.objects.filter(username=username).exists():
                messages.error(request, 'forgot_error:No account found with that username')
            elif new_pass != confirm:
                messages.error(request, 'forgot_error:Passwords do not match')
            elif len(new_pass) < 6:
                messages.error(request, 'forgot_error:Password must be at least 6 characters')
            else:
                user = User.objects.get(username=username)
                user.set_password(new_pass)
                user.save()
                messages.success(request, 'forgot_success:Password reset! You can now log in.')

    return render(request, 'auth.html')


def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('auth')
    return render(request, 'dashboard.html')


def chatbot_view(request):
    if not request.user.is_authenticated:
        return redirect('auth')
    return render(request, 'chatbot.html')

def logout_view(request):
    logout(request)
    return redirect('auth')