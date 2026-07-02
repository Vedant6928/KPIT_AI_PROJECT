from django.shortcuts import render, redirect
from django.contrib import messages

# Hardcoded credentials
VALID_ID = "admin123"
VALID_PASSWORD = "pass123"

def login_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('password')

        if user_id == VALID_ID and password == VALID_PASSWORD:
            request.session['logged_in'] = True
            return redirect('index')  # change to your actual landing page name
        else:
            messages.error(request, 'Invalid ID or Password')
            return redirect('login')

    return render(request, 'login.html')


def forgot_password_view(request):
    return render(request, 'forgot_password.html')


def dashboard_view(request):
    if not request.session.get('logged_in'):
        return redirect('login')
    return render(request, 'dashboard.html')


def logout_view(request):
    request.session.flush()
    return redirect('login')

def index_view(request):
    return render(request, 'index.html')
