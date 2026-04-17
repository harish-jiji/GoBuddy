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
import random
import decimal
from datetime import timedelta

from core.models import Booking, Package, Message, Destination, PaymentTransaction, SavedCard
from customers.models import TripPlan, UserProfile


# ============================================================
# CUSTOMER DASHBOARD
# ============================================================
from django.db.models import Sum, Count

@login_required(login_url='core:signin')
def dashboard(request):
    recent_bookings = Booking.objects.filter(user=request.user).order_by('-created_at')[:10]
    # Use paid_amount for revenue/spent calculation as requested
    total_spent = Booking.objects.filter(user=request.user).aggregate(total=Sum('paid_amount'))['total'] or 0

    upcoming_bookings = Booking.objects.filter(
        user=request.user,
        start_date__gte=timezone.now()
    ).order_by('start_date')

    trips_count = Booking.objects.filter(user=request.user).count()

    popular_destinations = Destination.objects.filter(is_active=True).order_by('-created_at')[:6]
    
    # RECOMMENDED PACKAGES (Filtered by user preference if profile exists)
    # Fix: User travel_companions matches package target_audience better
    user_comp = getattr(request.user.profile, 'travel_companions', None)
    
    recommended_packages = Package.objects.filter(is_active=True)
    if user_comp:
        # Match 'solo' with 'single' for target_audience mapping
        lookup = 'single' if user_comp == 'solo' else user_comp
        recommended_packages = recommended_packages.filter(target_audience=lookup)
    
    # If no results based on companions, fallback
    if recommended_packages.count() < 3:
        recommended_packages = Package.objects.filter(is_active=True)
        
    recommended_packages = recommended_packages.order_by('-created_at')[:6]

    # POPULAR PACKAGES (By most bookings)
    popular_packages = Package.objects.filter(is_active=True).annotate(
        booking_count=Count('booking')
    ).order_by('-booking_count')[:6]

    latest_trip = TripPlan.objects.filter(user=request.user).order_by('-id').first()

    return render(request, 'customers/US_Dashboard.html', {
        'user': request.user,
        'recent_bookings': recent_bookings,
        'upcoming_bookings': upcoming_bookings,
        'trips_count': trips_count,
        'total_spent': total_spent,
        'popular_destinations': popular_destinations,
        'recommended_packages': recommended_packages,
        'popular_packages': popular_packages,
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

    # Parse itinerary JSON
    itinerary_raw = request.POST.get("itinerary_json", "[]")
    try:
        itinerary = json.loads(itinerary_raw) if isinstance(itinerary_raw, str) else itinerary_raw
    except (ValueError, TypeError, json.JSONDecodeError):
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






@login_required(login_url='core:signin')
def trip_detail(request, trip_id):
    try:
        trip = TripPlan.objects.get(id=trip_id, user=request.user)
    except TripPlan.DoesNotExist:
        messages.info(request, "This trip plan no longer exists.")
        return redirect("customers:US_Dashboard")
        
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
    try:
        trip = TripPlan.objects.get(id=trip_id, user=request.user)
    except TripPlan.DoesNotExist:
        messages.warning(request, "This trip plan is no longer available.")
        return redirect("customers:US_Dashboard")

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
            try:
                dest_ids_list = [int(id.strip()) for id in destination_ids.split(',') if id.strip()]
                trip.destinations.set(Destination.objects.filter(id__in=dest_ids_list))
            except (ValueError, TypeError):
                pass

        # ---------- ITINERARY ----------
        itinerary_json = request.POST.get("itinerary_json")
        if itinerary_json:
            try:
                trip.itinerary = json.loads(itinerary_json)
            except (ValueError, TypeError, json.JSONDecodeError):
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
    # Try to get the trip, if not found (already deleted), redirect to dashboard
    try:
        trip = TripPlan.objects.get(id=trip_id, user=request.user)
    except TripPlan.DoesNotExist:
        messages.warning(request, "Trip plan not found or already deleted.")
        return redirect("customers:US_Dashboard")

    if request.method == "POST":
        trip.delete()
        messages.success(request, "Trip deleted successfully!")
        return redirect("customers:US_Dashboard")

    return render(request, "customers/confirm_delete_trip.html", {"trip": trip})


# ============================================================
# CONVERT TRIP TO BOOKING
# ============================================================
@login_required(login_url='core:signin')
def convert_trip(request, trip_id):
    try:
        trip = TripPlan.objects.get(id=trip_id, user=request.user)
    except TripPlan.DoesNotExist:
        messages.warning(request, "This trip plan is no longer available.")
        return redirect("customers:US_Dashboard")

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


@login_required(login_url='core:signin')
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if booking.status not in ['pending', 'confirmed']:
        messages.error(request, "This booking cannot be cancelled in its current state.")
        return redirect('customers:bookings')
    
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        messages.success(request, "Booking cancelled successfully.")
    return redirect('customers:bookings')


# ============================================================
# INBOX
# ============================================================
@login_required(login_url='core:signin')
def inbox(request):
    filter_type = request.GET.get('filter', 'all')
    all_messages = Message.objects.filter(user=request.user).order_by('-created_at')
    
    # Get total and unread counts for stats cards
    total_messages = all_messages.count()
    unread_count = all_messages.filter(is_read=False).count()
    
    # Get category counts for filter tabs
    bookings_count = all_messages.filter(category='bookings').count()
    payments_count = all_messages.filter(category='payments').count()
    offers_count = all_messages.filter(category='offers').count()
    system_count = all_messages.filter(category='system').count()
    
    # Apply filtering to the main list
    messages_list = all_messages
    if filter_type != 'all':
        messages_list = all_messages.filter(category=filter_type)
    
    latest_trip = TripPlan.objects.filter(user=request.user).order_by('-id').first()

    return render(request, 'customers/Inbox.html', {
        'user_messages': messages_list,
        'latest_trip': latest_trip,
        'filter': filter_type,
        'total_messages': total_messages,
        'unread_count': unread_count,
        'bookings_count': bookings_count,
        'payments_count': payments_count,
        'offers_count': offers_count,
        'system_count': system_count,
    })

@login_required(login_url='core:signin')
def message_detail(request, message_id):
    message = get_object_or_404(Message, id=message_id, user=request.user)
    message.is_read = True
    message.save()
    return render(request, 'customers/message_detail.html', {'msg': message})

@login_required(login_url='core:signin')
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id, user=request.user)
    message.delete()
    messages.success(request, "Message deleted successfully.")
    return redirect('customers:inbox')

# ============================================================
# PAYMENT SYSTEM (MOCK)
# ============================================================
import random
from django.utils import timezone
from datetime import timedelta

@login_required(login_url='core:signin')
def initiate_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.status not in ['confirmed', 'paid', 'completed']:
        messages.warning(request, "This booking is not available for payment.")
        return redirect('customers:bookings')
    
    if booking.payment_status == 'completed':
        messages.info(request, "This booking is already fully paid.")
        return redirect('customers:bookings')

    # Calculate EMI installments if any
    transactions = booking.transactions.all().order_by('-transaction_date')
    saved_cards = request.user.saved_cards.all()
    
    # Estimate next payment amount
    if booking.payment_method == 'emi' and booking.emi_installments > 0:
        next_amount = booking.final_total_amount / booking.emi_installments
    else:
        next_amount = booking.pending_amount

    return render(request, 'customers/pay_booking.html', {
        'booking': booking,
        'transactions': transactions,
        'saved_cards': saved_cards,
        'next_amount': next_amount,
    })

@login_required(login_url='core:signin')
def send_payment_otp(request, booking_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=400)
    
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    # Card handling
    saved_card_id = request.POST.get('saved_card_id')
    card_number = ""
    last_4 = ""
    
    if saved_card_id:
        try:
            saved_card = SavedCard.objects.get(id=saved_card_id, user=request.user)
            last_4 = saved_card.last_4
        except SavedCard.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Saved card not found'})
    else:
        # Traditional card details validation
        card_number = request.POST.get('card_number', '').replace(' ', '')
        expiry_date = request.POST.get('expiry_date', '') 
        cvv = request.POST.get('cvv', '')
        
        if len(card_number) < 13 or len(card_number) > 19:
            return JsonResponse({'success': False, 'message': 'Invalid Card Number'})
        
        last_4 = card_number[-4:]

        if not expiry_date or '/' not in expiry_date:
            return JsonResponse({'success': False, 'message': 'Invalid Expiry'})
        
        if len(cvv) < 3 or len(cvv) > 4:
            return JsonResponse({'success': False, 'message': 'Invalid CVV'})

    # Amount to be paid in this session
    payment_choice = request.POST.get('payment_choice') # Only on first pay
    payment_type = request.POST.get('payment_type', 'installment') # 'installment' or 'full'
    emi_installments = int(request.POST.get('emi_installments', 2))
    
    amount_to_pay = 0.0
    final_total = float(booking.total_amount)
    
    if booking.paid_amount == 0:
        # Initial choice handling
        if payment_choice == 'emi':
            if emi_installments > 2:
                final_total = float(booking.total_amount) * 1.05
            amount_to_pay = final_total / emi_installments
        else:
            amount_to_pay = final_total
    else:
        # Subsequent payment
        if payment_type == 'full':
            amount_to_pay = float(booking.pending_amount)
        else:
            amount_to_pay = float(booking.final_total_amount / booking.emi_installments)
    
    # Store temporary state in session for verification
    request.session[f'pending_pay_{booking.id}'] = {
        'amount': amount_to_pay,
        'final_total': final_total if booking.paid_amount == 0 else float(booking.final_total_amount),
        'payment_method': 'emi' if (payment_choice == 'emi' or booking.payment_method == 'emi') else 'full',
        'emi_installments': emi_installments if booking.paid_amount == 0 else booking.emi_installments,
        'card_last_4': last_4,
        'save_card': request.POST.get('save_card') == 'on',
        'card_holder': request.POST.get('card_holder', ''),
        'expiry': request.POST.get('expiry_date', ''),
        'card_number': card_number # needed only if saving new
    }

    # Generate OTP
    otp = str(random.randint(100000, 999999))
    booking.otp = otp
    booking.otp_expiry = timezone.now() + timedelta(minutes=1)
    booking.save()
    
    # Send OTP
    Message.objects.create(
        user=request.user,
        category='payments',
        subject='Verification OTP',
        body=f'Your OTP for paying ₹{amount_to_pay:,.2f} on booking {booking.booking_reference} is {otp}. Expires in 1 min.'
    )
    
    return JsonResponse({
        'success': True, 
        'message': 'OTP sent. Check inbox.',
        'amount': amount_to_pay
    })

@login_required(login_url='core:signin')
def verify_payment_otp(request, booking_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'}, status=400)
    
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    otp_input = request.POST.get('otp', '')
    
    pay_data = request.session.get(f'pending_pay_{booking.id}')
    if not pay_data:
        return JsonResponse({'success': False, 'message': 'Session expired. Try again.'})

    if not booking.otp or not booking.otp_expiry or timezone.now() > booking.otp_expiry:
        return JsonResponse({'success': False, 'message': 'OTP expired.'})
    
    if otp_input == booking.otp:
        amount = pay_data['amount']
        
        # On first payment, set the plan
        if booking.paid_amount == 0:
            booking.payment_method = pay_data['payment_method']
            booking.emi_installments = pay_data['emi_installments']
            booking.final_total_amount = decimal.Decimal(str(pay_data['final_total']))

        # Create Transaction
        PaymentTransaction.objects.create(
            booking=booking,
            amount=amount,
            payment_method='Card',
            card_last_4=pay_data['card_last_4']
        )
        
        # Update Booking
        booking.paid_amount += decimal.Decimal(str(amount))
        
        if booking.pending_amount <= 0:
            booking.payment_status = 'completed'
            booking.status = 'paid'
        else:
            booking.payment_status = 'partial'
            booking.status = 'paid' # Keep as paid/active once first payment is done
            
        booking.otp = None 
        booking.save()
        
        # Save Card if requested and new
        if pay_data.get('save_card') and pay_data.get('card_number'):
            SavedCard.objects.get_or_create(
                user=request.user,
                last_4=pay_data['card_last_4'],
                expiry_date=pay_data['expiry'],
                defaults={'card_holder': pay_data['card_holder']}
            )
        
        # Clean session
        del request.session[f'pending_pay_{booking.id}']

        # Success Message
        Message.objects.create(
            user=request.user,
            category='payments',
            subject='Payment Successful',
            body=f'Your payment for booking {booking.booking_reference} has been completed successfully! Debited rs {amount:,.2f}.'
        )
        
        return JsonResponse({'success': True, 'message': f'Success! ₹{amount:,.2f} debited.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid OTP.'})


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
        new_username = request.POST.get("username", "").strip()
        if new_username:
            user.username = new_username.lower() # lowercase enforced
            
        user.email = request.POST.get("email", user.email)
        dob = request.POST.get("date_of_birth")
        if dob:
            user.date_of_birth = dob
        user.save()

        # PROFILE fields
        profile.phone = request.POST.get("phone", profile.phone)
        profile.location = request.POST.get("location", profile.location)
        profile.bio = request.POST.get("bio", profile.bio)

        if request.FILES.get("profile_image"):
            profile.profile_image = request.FILES["profile_image"]

        profile.save()
        messages.success(request, "General profile settings updated!")
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
    })


@login_required(login_url='core:signin')
def security_settings(request):
    """View and update security questions and passwords"""
    profile = request.user.profile
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "questions":
            profile.security_q1 = request.POST.get("q1")
            profile.security_a1 = request.POST.get("a1", "").lower().strip()
            profile.security_q2 = request.POST.get("q2")
            profile.security_a2 = request.POST.get("a2", "").lower().strip()
            profile.security_q3 = request.POST.get("q3")
            profile.security_a3 = request.POST.get("a3", "").lower().strip()
            profile.save()
            messages.success(request, "Security questions updated!")
        
        elif action == "password":
            from django.contrib.auth import update_session_auth_hash
            from django.contrib.auth.forms import PasswordChangeForm
            form = PasswordChangeForm(request.user, request.POST)
            if form.is_valid():
                user = form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Password changed successfully!")
            else:
                messages.error(request, "Please correct the error below.")

        return redirect("customers:security_settings")
        
    return render(request, "customers/Security.html", {"profile": profile})


@login_required(login_url='core:signin')
def privacy_settings(request):
    """Update privacy preferences"""
    profile = request.user.profile
    if request.method == "POST":
        profile.privacy_level = request.POST.get("privacy_level", profile.privacy_level)
        profile.save()
        messages.success(request, "Privacy settings updated!")
        return redirect("customers:privacy_settings")
        
    return render(request, "customers/Privacy.html", {"profile": profile})


@login_required(login_url='core:signin')
def notification_settings(request):
    """Update notification choices"""
    profile = request.user.profile
    if request.method == "POST":
        profile.email_notifications = 'email_notif' in request.POST
        profile.booking_updates = 'booking_notif' in request.POST
        profile.payment_alerts = 'payment_notif' in request.POST
        profile.special_offers = 'offers_notif' in request.POST
        profile.save()
        messages.success(request, "Notification preferences updated!")
        return redirect("customers:notification_settings")
        
    return render(request, "customers/Notifications.html", {"profile": profile})


@login_required(login_url='core:signin')
def friends_list(request):
    """View friends and incoming requests"""
    from django.db.models import Q
    from .models import Friendship
    
    # Friends: where status is accepted
    friends = Friendship.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status='accepted'
    )
    
    incoming_requests = Friendship.objects.filter(to_user=request.user, status='pending')
    outgoing_requests = Friendship.objects.filter(from_user=request.user, status='pending')
    
    return render(request, "customers/Friends.html", {
        "friends": friends,
        "incoming": incoming_requests,
        "outgoing": outgoing_requests
    })


@login_required(login_url='core:signin')
def search_friends(request):
    """Search for other users by username or email"""
    query = request.GET.get("q", "").strip().lower()
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    results = []
    if query:
        results = User.objects.filter(
            Q(email__icontains=query) | Q(username__icontains=query)
        ).exclude(id=request.user.id)
        
    return render(request, "customers/Friends_Search.html", {"results": results, "query": query})


@login_required(login_url='core:signin')
def send_friend_request(request, user_id):
    """Send an invitation to another user"""
    from .models import Friendship
    from django.contrib.auth import get_user_model
    User = get_user_model()
    to_user = get_object_or_404(User, id=user_id)
    
    # Check if request exists
    if Friendship.objects.filter(from_user=request.user, to_user=to_user).exists():
        messages.info(request, "Request already sent.")
    else:
        Friendship.objects.create(from_user=request.user, to_user=to_user)
        messages.success(request, "Friend request sent!")
        
    return redirect("customers:friends_list")


@login_required(login_url='core:signin')
def accept_friend_request(request, request_id):
    from .models import Friendship
    friend_request = get_object_or_404(Friendship, id=request_id, to_user=request.user)
    friend_request.status = 'accepted'
    friend_request.save()
    messages.success(request, "Friend request accepted!")
    return redirect("customers:friends_list")


@login_required(login_url='core:signin')
def reject_friend_request(request, request_id):
    from .models import Friendship
    friend_request = get_object_or_404(Friendship, id=request_id, to_user=request.user)
    friend_request.status = 'rejected'
    friend_request.save()
    messages.info(request, "Friend request rejected.")
    return redirect("customers:friends_list")


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
    
    # RECOMMENDED PACKAGES (Filtered by user preference if profile exists)
    user_comp = getattr(request.user.profile, 'travel_companions', None)
    recommended_packages = Package.objects.filter(is_active=True)
    if user_comp:
        lookup = 'single' if user_comp == 'solo' else user_comp
        recommended_packages = recommended_packages.filter(target_audience=lookup)
    
    if recommended_packages.count() < 3:
        recommended_packages = Package.objects.filter(is_active=True)
        
    recommended_packages = recommended_packages.order_by('-created_at')[:3]

    return render(request, 'customers/my_trips.html', {
        'trip_plans': qs,
        'status_filter': status_filter,
        'recommended_packages': recommended_packages,
    })


# ============================================================
# SUBMIT FOR APPROVAL
# ============================================================
@login_required(login_url='core:signin')
def submit_for_approval(request, trip_id):
    """Submit a draft trip plan for admin approval"""
    try:
        trip = TripPlan.objects.get(id=trip_id, user=request.user)
    except TripPlan.DoesNotExist:
        messages.warning(request, "This trip plan is no longer available.")
        return redirect("customers:US_Dashboard")
    
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
    try:
        trip = TripPlan.objects.get(id=trip_id, user=request.user)
    except TripPlan.DoesNotExist:
        messages.warning(request, "This trip plan is no longer available.")
        return redirect("customers:US_Dashboard")
    
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
    try:
        trip = TripPlan.objects.get(id=trip_id, user=request.user)
    except TripPlan.DoesNotExist:
        messages.warning(request, "This trip plan is no longer available.")
        return redirect("customers:US_Dashboard")
    
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
    try:
        trip = TripPlan.objects.get(id=trip_id, user=request.user)
    except TripPlan.DoesNotExist:
        messages.warning(request, "This trip plan is no longer available.")
        return redirect("customers:US_Dashboard")
    
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
    sort_by = request.GET.get('sort', 'newest')
    
    # Get pre-planned packages that are available and active
    qs = Package.objects.filter(
        is_preplanned=True,
        available_for_booking=True,
        is_active=True
    ).prefetch_related('destinations')
    
    if category_filter != 'all':
        qs = qs.filter(category=category_filter)
        
    if sort_by == 'popular':
        qs = qs.annotate(booking_count=Count('booking')).order_by('-booking_count')
    else:
        qs = qs.order_by('-created_at')
    
    # Get customer's converted packages
    my_converted = Package.objects.filter(
        source_trip_plan__user=request.user,
        source_trip_plan__isnull=False
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
        category = request.POST.get('category', 'standard')
        notes = request.POST.get('notes', '')
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Invalid date format.')
                return redirect('customers:package_detail', package_id)

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
                booking_category=category,
                notes=notes,
                total_amount=total_amount,
                final_total_amount=total_amount,
                status='pending',
                payment_status='pending'
            )
            
            messages.success(
                request,
                f'Booking request sent! Once admin confirms, you can proceed to payment. Ref: {booking.booking_reference}'
            )
            return redirect('customers:bookings')
        else:
            messages.error(request, 'Please select a start date.')
            return redirect('customers:package_detail', package_id)
    
    return redirect('customers:package_detail', package_id)


@login_required(login_url='core:signin')
def payments_list(request):
    """View to list all payments and transaction history"""
    bookings_with_payments = Booking.objects.filter(
        user=request.user,
        status__in=['confirmed', 'paid', 'completed']
    ).order_by('-created_at')
    
    # Also get all transactions for a global history view
    transactions = PaymentTransaction.objects.filter(
        booking__user=request.user
    ).order_by('-transaction_date')

    return render(request, 'customers/Payments.html', {
        'bookings': bookings_with_payments,
        'transactions': transactions,
    })
