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
    try:
        destination = Destination.objects.get(url_name=url_name, is_active=True)
    except Destination.DoesNotExist:
        messages.info(request, "This destination is currently unavailable.")
        return redirect('core:home')
        
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
    try:
        package = Package.objects.get(pk=pk, is_active=True)
    except Package.DoesNotExist:
        messages.info(request, "This travel package is no longer available.")
        return redirect('core:home')
        
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
        username = request.POST.get('username', '').lower().strip()
        if username and User.objects.filter(username=username).exists():
            messages.error(request, "This username is already taken.")
            return redirect('core:signup')

        user = User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
            phone=phone,
            username=username
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


# ============================================================
# PASSWORD RECOVERY (SECURITY QUESTIONS)
# ============================================================
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if not user.profile.security_q1:
                 messages.error(request, "This account hasn't set up security questions. Please contact support.")
                 return redirect('core:forgot_password')
            return render(request, 'security_questions_challenge.html', {'user_id': user.id, 'user': user})
        except User.DoesNotExist:
            messages.error(request, "No user found with that email.")
    return render(request, 'forgot_password.html')

def verify_security_questions(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(User, id=user_id)
        
        a1 = request.POST.get('a1', '').lower().strip()
        a2 = request.POST.get('a2', '').lower().strip()
        a3 = request.POST.get('a3', '').lower().strip()
        
        # If any one answer matches
        if (a1 and a1 == user.profile.security_a1) or \
           (a2 and a2 == user.profile.security_a2) or \
           (a3 and a3 == user.profile.security_a3):
            request.session['reset_user_id'] = user.id
            return redirect('core:reset_password')
        else:
            messages.error(request, "Security answers do not match.")
            return render(request, 'security_questions_challenge.html', {'user_id': user.id, 'user': user})
    return redirect('core:forgot_password')

def reset_password(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('core:forgot_password')
    
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if password == confirm_password:
            user.set_password(password)
            user.save()
            del request.session['reset_user_id']
            messages.success(request, "Password reset successful. Please sign in.")
            return redirect('core:signin')
        else:
            messages.error(request, "Passwords do not match.")
            
    return render(request, 'reset_password.html', {'user': user})
