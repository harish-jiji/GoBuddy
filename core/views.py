# core/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.conf import settings
from .models import Destination, Package

User = get_user_model()


# ============================================================
# HOME PAGE (FINAL, USED BY index.html)
# ============================================================
def home(request):
    # Destinations (Top 6)
    featured = Destination.objects.filter(is_active=True)[:6]

    # Package categories (4 each)
    honeymoon = Package.objects.filter(is_active=True, category='honeymoon')[:4]
    family = Package.objects.filter(is_active=True, category='family')[:4]
    solo = Package.objects.filter(is_active=True, category='solo')[:4]
    friends = Package.objects.filter(is_active=True, category='friends')[:4]

    return render(request, 'index.html', {
        'featured': featured,
        'honeymoon': honeymoon,
        'family': family,
        'solo': solo,
        'friends': friends,
    })


# ============================================================
# DESTINATIONS LIST PAGE
# ============================================================
def destinations(request):
    destinations_list = Destination.objects.filter(is_active=True)
    return render(request, 'destinations.html', {
        'destinations': destinations_list
    })

# ============================================================
# DESTINATION DETAIL PAGE
# ============================================================
def destination_detail(request, url_name):
    destination = get_object_or_404(Destination, url_name=url_name, is_active=True)
    return render(request, 'destination_detail.html', {
        'destination': destination,
    })


# ============================================================
# PACKAGES (List view removed as per request)
# ============================================================
def packages_view(request):
    # Redirecting to home or showing 404 since list view is removed
    return redirect('core:home')


# ============================================================
# SINGLE PACKAGE DETAIL PAGE
# ============================================================
def package_detail(request, pk):
    package = get_object_or_404(Package, pk=pk, is_active=True)
    return render(request, 'package_detail.html', {
        'package': package
    })


# ============================================================
# CUSTOMERS – SIGNIN
# ============================================================
def signin(request):
    """
    Login for customers.
    GoUser uses email as the login username.
    """
    if request.method == 'POST':
        identifier = request.POST.get('email') or request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=identifier, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('customers:US_Dashboard')
            else:
                messages.error(request, "Account disabled.")
        else:
            messages.error(request, "Invalid email or password.")

        return redirect('core:signin')

    return render(request, 'signin.html')


# ============================================================
# CUSTOMERS – SIGNUP
# ============================================================
def signup(request):
    """
    Register a new customer using GoUser model.
    """
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        # Validation
        if not email or not password:
            messages.error(request, "Email and password are required.")
            return redirect('core:signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return redirect('core:signup')

        # Create the user
        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            phone=phone
        )
        user.save()

        messages.success(request, "Account created successfully! Please sign in.")
        return redirect('core:signin')

    return render(request, 'signup.html')


# ============================================================
# SIGNOUT
# ============================================================
def signout(request):
    logout(request)
    return redirect('core:signin')
