# customers/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
import json

from core.models import Booking, Package, Message, Destination
from customers.models import TripPlan, UserProfile


# ============================================================
# CUSTOMER DASHBOARD
# ============================================================
@login_required(login_url='core:signin')
def dashboard(request):
    recent_bookings = Booking.objects.filter(user=request.user).order_by('-created_at')[:10]
    total_spent = recent_bookings.aggregate(total_amount=Sum('total_amount'))['total_amount'] or 0

    upcoming_bookings = Booking.objects.filter(
        user=request.user,
        start_date__gte=timezone.now()
    ).order_by('start_date')

    trips_count = Booking.objects.filter(user=request.user).count()

    popular_destinations = Destination.objects.filter(is_active=True).order_by('-created_at')[:6]
    recommended_packages = Package.objects.filter(is_active=True).order_by('-created_at')[:6]

    latest_trip = TripPlan.objects.filter(user=request.user).order_by('-id').first()

    return render(request, 'customers/US_Dashboard.html', {
        'user': request.user,
        'recent_bookings': recent_bookings,
        'upcoming_bookings': upcoming_bookings,
        'trips_count': trips_count,
        'total_spent': total_spent,
        'popular_destinations': popular_destinations,
        'recommended_packages': recommended_packages,
        'latest_trip': latest_trip,
    })


# ============================================================
# DESTINATIONS LIST PAGE (CUSTOMER)
# ============================================================
@login_required(login_url='core:signin')
def destinations_list(request):
    destinations = Destination.objects.filter(is_active=True)
    latest_trip = TripPlan.objects.filter(user=request.user).order_by('-id').first()

    return render(request, 'customers/destinations.html', {
        'destinations': destinations,
        'latest_trip': latest_trip,
    })


# ============================================================
# DESTINATION DETAIL PAGE (CUSTOMER, WITH SIDEBAR)
# ============================================================
@login_required(login_url='core:signin')
def destination_detail(request, url_name):
    destination = get_object_or_404(Destination, url_name=url_name, is_active=True)
    latest_trip = TripPlan.objects.filter(user=request.user).order_by('-id').first()

    return render(request, 'customers/view/destination_detail.html', {
        'destination': destination,
        'latest_trip': latest_trip,
    })


# ============================================================
# BOOKINGS PAGE
# ============================================================
@login_required(login_url='core:signin')
def bookings_view(request):
    filter_type = request.GET.get("filter", "all")

    qs = Booking.objects.filter(user=request.user).order_by('-created_at')

    upcoming = qs.filter(start_date__gte=timezone.now())
    completed = qs.filter(status='completed')
    cancelled = qs.filter(status='cancelled')

    if filter_type == "upcoming":
        qs = upcoming
    elif filter_type == "completed":
        qs = completed
    elif filter_type == "cancelled":
        qs = cancelled

    latest_trip = TripPlan.objects.filter(user=request.user).order_by('-id').first()

    return render(request, 'customers/Bookings.html', {
        'bookings': qs,
        'upcoming_bookings': upcoming,
        'completed_bookings': completed,
        'cancelled_bookings': cancelled,
        'filter_type': filter_type,
        'latest_trip': latest_trip,
    })





# ============================================================
# SAVE TRIP
# ============================================================
@login_required(login_url='core:signin')
def save_trip(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid Method")

    # Handle multiple destinations
    destination_ids = request.POST.get("destination_ids", "")
    destination_ids_list = [int(id.strip()) for id in destination_ids.split(',') if id.strip()]
    
    if not destination_ids_list:
        messages.error(request, "Please select at least one destination.")
        return redirect("customers:plan_trips")
    
    # Get number of days
    number_of_days = request.POST.get("number_of_days", 1)
    try:
        number_of_days = int(number_of_days)
    except (ValueError, TypeError):
        number_of_days = 1

    # Parse JSON fields safely
    itinerary_raw = request.POST.get("itinerary_json", "[]")
    try:
        itinerary = json.loads(itinerary_raw) if isinstance(itinerary_raw, str) else itinerary_raw
    except Exception:
        itinerary = []

    # Parse itinerary JSON
    itinerary_raw = request.POST.get("itinerary_json", "[]")
    try:
        itinerary = json.loads(itinerary_raw) if isinstance(itinerary_raw, str) else itinerary_raw
    except Exception:
        itinerary = []
    
    # Get start and end locations
    start_location = request.POST.get("start_location") or None
    end_location = request.POST.get("end_location") or None
    
    # Create trip plan
    trip = TripPlan.objects.create(
        user=request.user,
        title=request.POST.get("title") or "My Trip Plan",
        number_of_days=number_of_days,
        start_date=request.POST.get("start_date") or None,
        travelers=request.POST.get("travelers") or 1,
        budget=request.POST.get("budget") or None,
        
        # Preferences
        travel_style=request.POST.get("travel_style"),
        accommodation=request.POST.get("accommodation"),
        transportation=request.POST.get("transportation"),
        meals=request.POST.get("meals"),
        
        start_location=start_location,
        end_location=end_location,
        itinerary=itinerary,
        status=request.POST.get("status", "draft"),  # Default to draft
    )

    # Add destinations (ManyToMany)
    destinations = Destination.objects.filter(id__in=destination_ids_list)
    trip.destinations.set(destinations)

    messages.success(request, "Trip plan saved successfully!")
    return redirect("customers:my_trips")  # Redirect to my trips page


# ============================================================
# PLAN TRIP ITINERARY (STEP 2)
# ============================================================
@login_required(login_url='core:signin')
def plan_trip_itinerary(request):
    # Get all available destinations
    destinations = Destination.objects.filter(is_active=True)
    
    # Serialize for JS
    destinations_data = list(destinations.values('id', 'name', 'state'))

    return render(request, "customers/plan_trip_itinerary.html", {
        "destinations": destinations,
        "destinations_data": destinations_data,
        "GOOGLE_MAPS_API_KEY": settings.GOOGLE_MAPS_API_KEY,
    })






# ============================================================
# TRIP DETAIL PAGE
# ============================================================
@login_required(login_url='core:signin')
def trip_detail(request, trip_id):
    trip = get_object_or_404(TripPlan, id=trip_id, user=request.user)
    latest_trip = TripPlan.objects.filter(user=request.user).order_by('-id').first()

    return render(request, "customers/trip_detail.html", {
        "trip": trip,
        "latest_trip": latest_trip,
    })


# ============================================================
# EDIT TRIP (FULL ITINERARY SUPPORT)
# ============================================================
@login_required(login_url='core:signin')
def edit_trip(request, trip_id):
    trip = get_object_or_404(TripPlan, id=trip_id, user=request.user)

    if request.method == "POST":

        # ---------- BASIC INFO ----------
        trip.title = request.POST.get("title", trip.title)

        if request.POST.get("start_date"):
            trip.start_date = request.POST.get("start_date")

        if request.POST.get("end_date"):
            trip.end_date = request.POST.get("end_date")

        travelers = request.POST.get("travelers")
        if travelers and travelers.isdigit():
            trip.travelers = int(travelers)

        # ---------- LOCATIONS ----------
        trip.start_location = request.POST.get("start_location", trip.start_location)
        trip.end_location = request.POST.get("end_location", trip.end_location)

        # ---------- DESTINATIONS ----------
        destination_ids = request.POST.get("destination_ids")
        if destination_ids:
            trip.destination_ids = destination_ids.split(",")

        # ---------- ITINERARY ----------
        itinerary_json = request.POST.get("itinerary_json")
        if itinerary_json:
            try:
                trip.itinerary_json = json.loads(itinerary_json)
            except Exception:
                pass

        # ---------- PREFERENCES ----------
        trip.travel_style = request.POST.get("travel_style", trip.travel_style)
        trip.accommodation = request.POST.get("accommodation", trip.accommodation)
        trip.transportation = request.POST.get("transportation", trip.transportation)
        trip.meals = request.POST.get("meals", trip.meals)

        # ---------- BUDGET ----------
        budget = request.POST.get("budget")
        if budget:
            try:
                trip.budget = int(float(budget))
            except ValueError:
                pass

        # ---------- STATUS ----------
        trip.status = request.POST.get("status", trip.status)

        # ---------- INTERESTS ----------
        trip.interests = request.POST.getlist("interests") or trip.interests

        # ---------- NOTES ----------
        trip.notes = request.POST.get("notes", trip.notes)

        trip.save()
        messages.success(request, "Trip updated successfully!")
        return redirect("customers:trip_detail", trip.id)

    # ---------- GET REQUEST ----------
    
    # Prepare data for JS
    import json
    trip_itinerary_json = json.dumps(trip.itinerary) if trip.itinerary else "[]"
    trip_destination_ids = list(trip.destinations.values_list('id', flat=True))
    if not trip_destination_ids and trip.destination:
        trip_destination_ids = [trip.destination.id]

    # Choices for Dropdowns (Fetched from DB/Model)
    activity_choices = [
        ('sightseeing', 'Sightseeing'),
        ('adventure', 'Adventure'),
        ('shopping', 'Shopping'),
        ('relaxation', 'Relaxation'),
        ('culture', 'Cultural'),
        ('food', 'Food/Dining'),
        ('other', 'Other'),
    ]
    transport_choices = TripPlan.TRANSPORTATION_CHOICES 

    destinations = Destination.objects.filter(is_active=True)
    destinations_data = list(destinations.values('id', 'name', 'state'))

    return render(request, "customers/edit_trip.html", {
        "trip": trip,
        "trip_itinerary_json": trip_itinerary_json,
        "trip_destination_ids": trip_destination_ids,
        "activity_choices": activity_choices,
        "transport_choices": transport_choices,
        "travel_style_choices": TripPlan.TRAVEL_STYLE_CHOICES,
        "accommodation_choices": TripPlan.ACCOMMODATION_CHOICES,
        "meal_choices": TripPlan.MEAL_CHOICES,
        "destinations": destinations, 
        "destinations_data": destinations_data,
    })



# ============================================================
# DELETE TRIP
# ============================================================
@login_required(login_url='core:signin')
def delete_trip(request, trip_id):
    trip = get_object_or_404(TripPlan, id=trip_id, user=request.user)

    # For safety, require POST to delete (if you want a GET-delete confirm page you can add it)
    if request.method == "POST":
        trip.delete()
        messages.success(request, "Trip deleted successfully!")
        return redirect("customers:plan_trips")

    # If GET, show a simple confirmation page (optional)
    return render(request, "customers/confirm_delete_trip.html", {"trip": trip})


# ============================================================
# CONVERT TRIP TO BOOKING
# ============================================================
@login_required(login_url='core:signin')
def convert_trip(request, trip_id):
    trip = get_object_or_404(TripPlan, id=trip_id, user=request.user)

    # Create a minimal Booking from TripPlan — adjust fields as your Booking model requires
    booking = Booking.objects.create(
        user=request.user,
        package=None,
        destination=trip.destination,
        start_date=trip.start_date,
        end_date=trip.end_date,
        total_amount=trip.budget or 0,
        status='upcoming'
    )

    messages.success(request, "Trip successfully converted into a booking!")
    return redirect("customers:bookings")


# ============================================================
# INBOX
# ============================================================
@login_required(login_url='core:signin')
def inbox(request):
    messages_list = Message.objects.filter(user=request.user).order_by('-created_at')
    latest_trip = TripPlan.objects.filter(user=request.user).order_by('-id').first()

    return render(request, 'customers/Inbox.html', {
        'messages': messages_list,
        'latest_trip': latest_trip,
    })


# ============================================================
# PROFILE PAGE
# ============================================================
@login_required(login_url='core:signin')
def profile(request):
    user = request.user
    # ensure related UserProfile exists (should be created by post_save signal)
    profile = getattr(user, "profile", None)
    if profile is None:
        profile = UserProfile.objects.create(user=user)

    if request.method == "POST":
        # USER fields
        user.full_name = request.POST.get("full_name", user.full_name)
        user.email = request.POST.get("email", user.email)
        dob = request.POST.get("date_of_birth")
        if dob:
            user.date_of_birth = dob
        user.save()

        # PROFILE fields
        profile.phone = request.POST.get("phone", profile.phone)
        profile.location = request.POST.get("location", profile.location)
        profile.bio = request.POST.get("bio", profile.bio)

        # file upload
        if request.FILES.get("profile_image"):
            profile.profile_image = request.FILES["profile_image"]

        profile.travel_style = request.POST.get("travel_style", profile.travel_style)
        profile.accommodation_preference = request.POST.get("accommodation", profile.accommodation_preference)
        profile.budget_range = request.POST.get("budget_range", profile.budget_range)
        profile.travel_companions = request.POST.get("companions", profile.travel_companions)

        profile.travel_interests = request.POST.getlist("interests")

        # Notifications & privacy flags (store booleans)
        profile.email_notifications = bool(request.POST.get("email_notifications"))
        profile.booking_updates = bool(request.POST.get("booking_updates"))
        profile.payment_alerts = bool(request.POST.get("payment_alerts"))
        profile.special_offers = bool(request.POST.get("special_offers"))

        profile.public_profile = bool(request.POST.get("public_profile"))
        profile.show_travel_history = bool(request.POST.get("show_travel_history"))
        profile.data_analytics = bool(request.POST.get("data_analytics"))

        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("customers:profile")

    interests_list = [
        "beaches", "mountains", "adventure", "food",
        "culture", "wildlife", "history", "nightlife"
    ]

    latest_trip = TripPlan.objects.filter(user=user).order_by('-id').first()

    return render(request, "customers/Profile.html", {
        "user": user,
        "profile": profile,
        "latest_trip": latest_trip,
        "profile_completion": getattr(profile, "profile_completion_percentage", 0),
        "interests_list": interests_list,
    })


# ============================================================
# MY TRIP PLANS
# ============================================================
@login_required(login_url='core:signin')
def my_trips(request):
    """List all customer's trip plans"""
    status_filter = request.GET.get('status', 'all')
    
    qs = TripPlan.objects.filter(user=request.user).order_by('-created_at')
    
    if status_filter != 'all':
        qs = qs.filter(status=status_filter)
    
    return render(request, 'customers/my_trips.html', {
        'trip_plans': qs,
        'status_filter': status_filter,
    })


# ============================================================
# SUBMIT FOR APPROVAL
# ============================================================
@login_required(login_url='core:signin')
def submit_for_approval(request, trip_id):
    """Submit a draft trip plan for admin approval"""
    trip = get_object_or_404(TripPlan, id=trip_id, user=request.user)
    
    if request.method == 'POST':
        if trip.status == 'draft':
            trip.status = 'pending'
            trip.save()
            
            # Notify admins
            admin_users = get_user_model().objects.filter(is_staff=True, is_superuser=True)
            for admin in admin_users:
                Message.objects.create(
                    user=admin,
                    category='trip_plans',
                    subject=f'New Trip Plan from {request.user.full_name or request.user.email}',
                    body=f'A new trip plan "{trip.title}" has been submitted for approval.'
                )
            
            messages.success(request, "Trip plan submitted for approval!")
        else:
            messages.warning(request, "This trip plan has already been submitted.")
        
        return redirect('customers:trip_detail', trip.id)
    
    return redirect('customers:trip_detail', trip.id)


# ============================================================
# ACCEPT ADMIN REVISION
# ============================================================
@login_required(login_url='core:signin')
def accept_admin_revision(request, trip_id):
    """Customer accepts admin's revised trip plan"""
    trip = get_object_or_404(TripPlan, id=trip_id, user=request.user)
    
    if trip.status == 'customer_review':
        trip.status = 'approved'
        trip.save()
        
        # Notify admin
        if trip.reviewed_by:
            Message.objects.create(
                user=trip.reviewed_by,
                category='trip_plans',
                subject=f'Customer accepted your revisions',
                body=f'{request.user.full_name or request.user.email} has accepted your revisions to trip plan "{trip.title}".'
            )
        
        messages.success(request, "You've accepted the admin's changes! You can now select your travel dates.")
        return redirect('customers:select_trip_dates', trip.id)
    else:
        messages.error(request, "This plan is not awaiting your review.")
        return redirect('customers:trip_detail', trip.id)


# ============================================================
# REJECT ADMIN REVISION
# ============================================================
@login_required(login_url='core:signin')
def reject_admin_revision(request, trip_id):
    """Customer rejects admin's revised trip plan"""
    trip = get_object_or_404(TripPlan, id=trip_id, user=request.user)
    
    if trip.status == 'customer_review':
        trip.status = 'draft'
        trip.admin_notes = ''
        trip.save()
        
        # Notify admin
        if trip.reviewed_by:
            Message.objects.create(
                user=trip.reviewed_by,
                category='trip_plans',
                subject=f'Customer rejected your revisions',
                body=f'{request.user.full_name or request.user.email} has rejected your revisions to trip plan "{trip.title}". The plan is back in draft status.'
            )
        
        messages.info(request, "Admin changes rejected. You can now edit and resubmit your plan.")
        return redirect('customers:edit_trip', trip.id)
    else:
        return redirect('customers:trip_detail', trip.id)


# ============================================================
# SELECT TRIP DATES
# ============================================================
@login_required(login_url='core:signin')
def select_trip_dates(request, trip_id):
    """Customer selects actual travel dates for submitted trip"""
    trip = get_object_or_404(TripPlan, id=trip_id, user=request.user)
    
    # Allow access after submit (pending) or approved status
    if trip.status not in ['pending', 'approved']:
        messages.error(request, "This trip plan must be submitted before selecting dates.")
        return redirect('customers:trip_detail', trip.id)
    
    if request.method == 'POST':
        from datetime import datetime, timedelta
        
        start_date_str = request.POST.get('start_date')
        itinerary_raw = request.POST.get('itinerary_json')

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = start_date + timedelta(days=trip.number_of_days - 1)
            
            trip.start_date = start_date
            trip.end_date = end_date
            
            # Update Itinerary if provided
            if itinerary_raw:
                try:
                    trip.itinerary = json.loads(itinerary_raw)
                except json.JSONDecodeError:
                    pass

            trip.save()
            
            messages.success(request, f"Travel dates and detailed itinerary confirmed! Your trip is scheduled from {start_date} to {end_date}.")
            return redirect('customers:trip_detail', trip.id)
        else:
            messages.error(request, "Please select a start date.")
    
    return render(request, 'customers/select_trip_dates.html', {
        'trip': trip,
        'today': timezone.now().date(),
    })


# ============================================================
# BROWSE PACKAGES
# ============================================================
@login_required(login_url='core:signin')
def browse_packages(request):
    """Browse pre-planned packages"""
    category_filter = request.GET.get('category', 'all')
    
    # Get pre-planned packages that are available and active
    qs = Package.objects.filter(
        is_preplanned=True,
        available_for_booking=True,
        is_active=True
    ).prefetch_related('destinations').order_by('-created_at')
    
    if category_filter != 'all':
        qs = qs.filter(category=category_filter)
    
    # Get customer's converted packages
    my_converted = Package.objects.filter(
        tripplan__user=request.user,
        tripplan__converted_to_package__isnull=False
    ).distinct()
    
    return render(request, 'customers/packages.html', {
        'packages': qs,
        'category_filter': category_filter,
        'my_converted_packages': my_converted,
    })


@login_required(login_url='core:signin')
def package_detail_view(request, package_id):
    """View package details"""
    package = get_object_or_404(
        Package,
        id=package_id,
        is_active=True,
        available_for_booking=True
    )
    
    return render(request, 'customers/package_detail.html', {
        'package': package,
        'today': timezone.now().date(),
    })


@login_required(login_url='core:signin')
def book_package(request, package_id):
    """Book a package"""
    package = get_object_or_404(
        Package,
        id=package_id,
        is_active=True,
        available_for_booking=True
    )
    
    if request.method == 'POST':
        from datetime import datetime, timedelta
        
        start_date_str = request.POST.get('start_date')
        travelers = int(request.POST.get('travelers', 1))
        
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = start_date + timedelta(days=package.duration_days - 1)
            
            # Calculate total amount
            total_amount = package.total_cost * travelers
            
            # Create booking
            booking = Booking.objects.create(
                user=request.user,
                package=package,
                start_date=start_date,
                end_date=end_date,
                travelers_count=travelers,
                total_amount=total_amount,
                status='pending',
                payment_status='pending'
            )
            
            messages.success(
                request,
                f'Package booked successfully! Booking reference: {booking.booking_reference}'
            )
            return redirect('customers:bookings')
        else:
            messages.error(request, 'Please select a start date.')
            return redirect('customers:package_detail', package_id)
    
    return redirect('customers:package_detail', package_id)
