# adminpanel/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib import messages
from django.urls import reverse
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils import timezone

from .permissions import is_admin_user, is_owner
from .forms import BookingFilterForm, AdminNoteForm
from .utils import queryset_to_csv_response
from .models import AdminNote, AdminConfiguration
from .forms import BookingFilterForm, AdminNoteForm, AdminConfigurationForm, PackageForm

# Concrete imports - we assume correct app loading order
from core.models import Destination, Booking, Package, Message
from customers.models import UserProfile

User = get_user_model()

# small decorator wrapper
def staff_and_group_required(view_func):
    decorated = login_required(user_passes_test(is_admin_user, login_url='adminpanel:manager_login')(view_func), login_url='adminpanel:manager_login')
    return decorated

def manager_login(request):
    if request.user.is_authenticated:
        if is_admin_user(request.user):
            return redirect('adminpanel:dashboard')
        return redirect('adminpanel:dashboard')

    if request.method == 'POST':
        email = request.POST.get('username') or request.POST.get('email')
        password = request.POST.get('password')
        code_input = request.POST.get('two_factor_code')
        
        # 1. Check User Credentials
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
             # 2. Check 2FA Code (Global)
            try:
                config = AdminConfiguration.objects.first()
                # If no config exists, create default '123456'
                if not config:
                    config = AdminConfiguration.objects.create(two_factor_code='123456')
                
                correct_code = config.two_factor_code
            except Exception:
                correct_code = '123456' # Fallback
            
            if code_input == correct_code:
                if is_admin_user(user):
                    login(request, user)
                    next_url = request.POST.get('next') or request.GET.get('next') or 'adminpanel:dashboard'
                    return redirect(next_url)
                else:
                    messages.error(request, "Access denied. Admin privileges required.")
            else:
                messages.error(request, "Invalid 2FA Verification Code.")
        else:
            messages.error(request, "Invalid email or password.")
            
    return render(request, 'admin/login.html')

@staff_and_group_required
@staff_and_group_required
def security_settings(request):
    # Only superuser can see/change the global 2FA code
    if not request.user.is_superuser:
        return render(request, 'admin/settings/security.html', {'is_superuser': False})

    config, created = AdminConfiguration.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        form = AdminConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.updated_by = request.user
            inst.save()
            messages.success(request, "Global 2FA code updated successfully.")
            return redirect('adminpanel:settings_security')
    else:
        form = AdminConfigurationForm(instance=config)
        
    return render(request, 'admin/settings/security.html', {'form': form, 'is_superuser': True})


@staff_and_group_required
def dashboard(request):
    total_users = User.objects.count()
    total_destinations = Destination.objects.count()
    total_packages = Package.objects.count()
    total_bookings = Booking.objects.count()

    revenue_total = Booking.objects.aggregate(total=Sum('total_amount'))['total'] or 0

    recent_bookings = Booking.objects.select_related('user', 'package').order_by('-created_at')[:10]
    recent_destinations = Destination.objects.order_by('-created_at')[:8]
    recent_notes = AdminNote.objects.select_related('booking', 'package', 'author').order_by('-created_at')[:8]

    # Prepare simpler chart data (last 7 days of bookings)
    days_range = 7
    end_date = timezone.now().date()
    start_date = end_date - timezone.timedelta(days=days_range - 1)
    
    analytics_data = (
        Booking.objects.filter(created_at__date__gte=start_date)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    
    chart_labels = []
    chart_data = []
    
    # Fill in missing days
    date_map = {entry['day']: entry['count'] for entry in analytics_data}
    for i in range(days_range):
        d = start_date + timezone.timedelta(days=i)
        chart_labels.append(d.strftime('%b %d'))
        chart_data.append(date_map.get(d, 0))

    context = {
        'total_users': total_users,
        'total_destinations': total_destinations,
        'total_packages': total_packages,
        'total_bookings': total_bookings,
        'revenue_total': revenue_total,
        'recent_bookings': recent_bookings,
        'recent_destinations': recent_destinations,
        'recent_notes': recent_notes,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'pending_plans_count': TripPlan.objects.filter(status='pending').count(),
    }
    return render(request, 'admin/AD_dashboard.html', context)


# -- DESTINATIONS (class-based)
class DestinationListView(ListView):
    model = Destination
    template_name = 'admin/destinations.html'
    context_object_name = 'destinations'
    paginate_by = 25
    ordering = ['-created_at']

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return redirect('adminpanel:manager_login')
        return super().dispatch(request, *args, **kwargs)


class DestinationCreateView(CreateView):
    model = Destination
    fields = ['name', 'url_name', 'country', 'state', 'description', 'image', 'price_per_day', 'best_season', 'latitude', 'longitude', 'is_active']
    template_name = 'admin/destination_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return redirect('adminpanel:manager_login')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, f'Destination "{form.cleaned_data["name"]}" has been created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('adminpanel:destinations')


class DestinationUpdateView(UpdateView):
    model = Destination
    fields = ['name', 'url_name', 'country', 'state', 'description', 'image', 'price_per_day', 'best_season', 'latitude', 'longitude', 'is_active']
    template_name = 'admin/destination_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return redirect('adminpanel:manager_login')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, f'Destination "{form.cleaned_data["name"]}" has been updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('adminpanel:destinations')


class DestinationDeleteView(DeleteView):
    model = Destination
    template_name = 'admin/destination_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        # Restrict delete to owner group or superuser
        if not is_owner(request.user):
            return redirect('adminpanel:destinations')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f'Destination "{obj.name}" has been deleted.')
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('adminpanel:destinations')


# -- PACKAGES
# -- PACKAGES
class PackageListView(ListView):
    model = Package
    template_name = 'admin/packages.html'
    context_object_name = 'packages'
    paginate_by = 25
    ordering = ['-created_at']

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return redirect('adminpanel:manager_login')
        return super().dispatch(request, *args, **kwargs)


class PackageCreateView(CreateView):
    model = Package
    form_class = PackageForm # Using the form we created
    template_name = 'admin/package_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return redirect('adminpanel:manager_login')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        destinations = Destination.objects.filter(is_active=True).order_by('name')
        context['all_destinations'] = destinations
        context['destinations_data'] = list(destinations.values('id', 'name', 'state', 'image', 'price_per_day'))
        return context

    def form_valid(self, form):
        import json
        
        form.instance.created_by = self.request.user
        
        # Handle itinerary JSON
        itinerary_json = self.request.POST.get('itinerary', '[]')
        try:
            form.instance.itinerary = json.loads(itinerary_json) if itinerary_json else []
        except:
            form.instance.itinerary = []
        
        # Save the package first
        response = super().form_valid(form)
        
        # Handle destinations M2M
        destinations_ids = self.request.POST.get('destinations', '')
        if destinations_ids:
            dest_ids = [int(id.strip()) for id in destinations_ids.split(',') if id.strip()]
            form.instance.destinations.set(Destination.objects.filter(id__in=dest_ids))
        
        messages.success(self.request, f'Package "{form.cleaned_data["name"]}" created successfully!')
        return response

    def get_success_url(self):
        return reverse('adminpanel:packages')


class PackageUpdateView(UpdateView):
    model = Package
    form_class = PackageForm
    template_name = 'admin/package_form.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return redirect('adminpanel:manager_login')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        destinations = Destination.objects.filter(is_active=True).order_by('name')
        context['all_destinations'] = destinations
        context['destinations_data'] = list(destinations.values('id', 'name', 'state', 'image', 'price_per_day'))
        return context

    def form_valid(self, form):
        import json
        
        # Handle itinerary JSON
        itinerary_json = self.request.POST.get('itinerary', '[]')
        try:
            form.instance.itinerary = json.loads(itinerary_json) if itinerary_json else []
        except:
            form.instance.itinerary = form.instance.itinerary or []
        
        # Save the package first
        response = super().form_valid(form)
        
        # Handle destinations M2M
        destinations_ids = self.request.POST.get('destinations', '')
        if destinations_ids:
            dest_ids = [int(id.strip()) for id in destinations_ids.split(',') if id.strip()]
            form.instance.destinations.set(Destination.objects.filter(id__in=dest_ids))
        
        messages.success(self.request, f'Package "{form.cleaned_data["name"]}" updated successfully!')
        return response

    def get_success_url(self):
        return reverse('adminpanel:packages')


class PackageDeleteView(DeleteView):
    model = Package
    template_name = 'admin/package_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        if not is_owner(request.user):
            return redirect('adminpanel:packages')
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f'Package "{obj.name}" has been deleted.')
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('adminpanel:packages')


@staff_and_group_required
def package_detail(request, pk):
    try:
        package = Package.objects.get(pk=pk)
    except Package.DoesNotExist:
        messages.warning(request, "This package no longer exists.")
        return redirect('adminpanel:packages')
    related_bookings = Booking.objects.filter(package=package).select_related('user').order_by('-created_at')[:50]
    
    # Handle Note Post
    if request.method == 'POST':
        form = AdminNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.author = request.user
            note.package = package
            note.save()
            return redirect('adminpanel:package_detail', pk=pk)
    else:
        form = AdminNoteForm()

    return render(request, 'admin/package_detail.html', {
        'package': package, 
        'related_bookings': related_bookings,
        'note_form': form
    })


# -- BOOKINGS
class BookingListView(ListView):
    model = Booking
    template_name = 'admin/bookings.html'
    context_object_name = 'bookings'
    paginate_by = 25

    def get_queryset(self):
        qs = Booking.objects.select_related('user', 'package').order_by('-created_at')
        
        status = self.request.GET.get('status')
        user_term = self.request.GET.get('user_search')
        start = self.request.GET.get('start_date')
        end = self.request.GET.get('end_date')
        
        if status:
            qs = qs.filter(status__iexact=status)
        if user_term:
            qs = qs.filter(Q(user__email__icontains=user_term) | Q(user__full_name__icontains=user_term))
        if start:
            qs = qs.filter(created_at__date__gte=start)
        if end:
            qs = qs.filter(created_at__date__lte=end)
            
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Pass the filter form with data to maintain state
        ctx['filter_form'] = BookingFilterForm(self.request.GET)
        return ctx

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return redirect('adminpanel:manager_login')
        return super().dispatch(request, *args, **kwargs)


class BookingDetailView(DetailView):
    model = Booking
    template_name = 'admin/booking_detail.html'
    context_object_name = 'booking'
    pk_url_kwarg = 'pk'

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
            return redirect('adminpanel:manager_login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['note_form'] = AdminNoteForm()
        # Travelers
        ctx['travelers'] = self.object.travelers.all()
        return ctx

    def post(self, request, *args, **kwargs):
        booking = self.get_object()
        form = AdminNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.author = request.user
            note.booking = booking
            note.save()
            return redirect('adminpanel:booking_detail', pk=booking.pk)
        
        # If invalid, re-render
        ctx = self.get_context_data()
        ctx['note_form'] = form
        return self.render_to_response(ctx)


@staff_and_group_required
def booking_approve(request, pk):
    """Confirm a booking and allow user to pay"""
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        booking.status = 'confirmed'
        booking.save()
        
        # Notify user
        Message.objects.create(
            user=booking.user,
            category='bookings',
            subject='Booking Confirmed - Payment Required',
            body=f'Your booking for {booking.package.name if booking.package else "Trip"} has been confirmed by our team. Please proceed to the payment page to complete your booking. Ref: {booking.booking_reference}'
        )
        
        messages.success(request, f"Booking {booking.booking_reference} confirmed!")
        return redirect('adminpanel:booking_detail', pk=pk)
    return redirect('adminpanel:booking_detail', pk=pk)


@staff_and_group_required
def booking_reject(request, pk):
    """Cancel/Reject a booking"""
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        
        # Notify user
        Message.objects.create(
            user=booking.user,
            category='bookings',
            subject='Booking Request Cancelled',
            body=f'We regret to inform you that your booking for {booking.package.name if booking.package else "Trip"} could not be confirmed at this time and has been cancelled. Ref: {booking.booking_reference}'
        )
        
        messages.info(request, f"Booking {booking.booking_reference} cancelled.")
        return redirect('adminpanel:booking_detail', pk=pk)
    return redirect('adminpanel:booking_detail', pk=pk)


@staff_and_group_required
def export_bookings_csv(request):
    qs = Booking.objects.select_related('user', 'package').order_by('-created_at')
    
    # Apply same filters if needed (omitted for brevity, can parse request.GET)
    
    header = ['PK', 'Booking Reference', 'User', 'User Email', 'Package', 'Status', 'Total Amount', 'Start Date', 'Created At']
    def rows():
        for b in qs:
            user_name = b.user.full_name or "N/A"
            user_email = b.user.email
            pkg_name = b.package.name if b.package else "Custom/Deleted"
            
            yield [
                b.pk,
                b.booking_reference,
                user_name,
                user_email,
                pkg_name,
                b.get_status_display(),
                b.total_amount,
                b.start_date,
                b.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
    return queryset_to_csv_response(qs, header, rows(), filename="bookings_export.csv")


# -- USERS
@staff_and_group_required
def users_list(request):
    qs = User.objects.order_by('-date_joined')
    
    search_term = request.GET.get('q')
    if search_term:
        qs = qs.filter(Q(email__icontains=search_term) | Q(full_name__icontains=search_term))
        
    paginator = Paginator(qs, 50)
    page = request.GET.get('page')
    return render(request, 'admin/users.html', {'users': paginator.get_page(page), 'search_term': search_term})


# -- EXPENSES (Placeholder)
@staff_and_group_required
def expenses_list(request):
    return render(request, 'admin/expenses.html', {
        'no_expense_model': True
    })

# Add Admin User View
class AdminCreateView(CreateView):
    model = User
    form_class = AdminConfigurationForm # Wait, mistake in copy paste, should be AdminCreationForm. Correcting below.
    template_name = 'admin/admin_create.html'
    
    def get_form_class(self):
        # We need to import it properly inside or ensure it's imported at top. 
        # For now, let's assume it's imported.
        from .forms import AdminCreationForm
        return AdminCreationForm

    def dispatch(self, request, *args, **kwargs):
        if not is_admin_user(request.user):
             return redirect('adminpanel:manager_login')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "New Admin user created successfully.")
        return reverse('adminpanel:users')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Admin'
        return context


# -- ANALYTICS
@staff_and_group_required
def analytics(request):
    days_range = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timezone.timedelta(days=days_range - 1)
    
    daily_bookings = (
        Booking.objects.filter(created_at__date__gte=start_date)
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(count=Count('id'), total=Sum('total_amount'))
        .order_by('day')
    )
    
    dates = []
    counts = []
    revenues = []
    
    data_map = {d['day']: d for d in daily_bookings}
    
    for i in range(days_range):
        d = start_date + timezone.timedelta(days=i)
        dates.append(d.strftime('%Y-%m-%d'))
        row = data_map.get(d, {'count': 0, 'total': 0})
        counts.append(row['count'])
        revenues.append(float(row['total'] or 0))
        
    return render(request, 'admin/analytics.html', {
        'dates': dates, 
        'counts': counts, 
        'revenues': revenues,
        'days_range': days_range
    })


# ============================================================
# TRIP PLAN MANAGEMENT
# ============================================================
from customers.models import TripPlan

@staff_and_group_required
def trip_plans_list(request):
    """List all customer trip plans with filtering"""
    status_filter = request.GET.get('status', 'all')
    search = request.GET.get('search', '')
    
    qs = TripPlan.objects.select_related('user').prefetch_related('destinations').order_by('-created_at')
    
    if status_filter != 'all':
        qs = qs.filter(status=status_filter)
    
    if search:
        qs = qs.filter(
            Q(title__icontains=search) | 
            Q(user__email__icontains=search) | 
            Q(user__full_name__icontains=search)
        )
    
    # Count by status
    pending_count = TripPlan.objects.filter(status='pending').count()
    approved_count = TripPlan.objects.filter(status='approved').count()
    rejected_count = TripPlan.objects.filter(status='rejected').count()
    
    paginator = Paginator(qs, 25)
    page = request.GET.get('page')
    
    return render(request, 'admin/trip_plans.html', {
        'trip_plans': paginator.get_page(page),
        'status_filter': status_filter,
        'search': search,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    })


@staff_and_group_required
def trip_plan_review(request, pk):
    """Review and manage a specific trip plan"""
    try:
        trip_plan = TripPlan.objects.get(pk=pk)
    except TripPlan.DoesNotExist:
        messages.warning(request, "This trip plan has been deleted or is unavailable.")
        return redirect('adminpanel:trip_plans')
    
    return render(request, 'admin/trip_plan_review.html', {
        'trip_plan': trip_plan,
    })


@staff_and_group_required
def trip_plan_approve(request, pk):
    """Approve a trip plan"""
    try:
        trip_plan = TripPlan.objects.get(pk=pk)
    except TripPlan.DoesNotExist:
        messages.warning(request, "This trip plan no longer exists.")
        return redirect('adminpanel:trip_plans')
    
    if request.method == 'POST':
        trip_plan.status = 'approved'
        trip_plan.reviewed_by = request.user
        trip_plan.reviewed_at = timezone.now()
        trip_plan.admin_notes = request.POST.get('admin_notes', '')
        trip_plan.save()
        
        # Notify customer
        Message.objects.create(
            user=trip_plan.user,
            category='trip_plans',
            subject=f'Your trip plan "{trip_plan.title}" has been approved!',
            body=f'Great news! Your trip plan has been approved. You can now select your travel dates and proceed to booking.\n\nAdmin notes: {trip_plan.admin_notes}'
        )
        
        messages.success(request, f'Trip plan "{trip_plan.title}" has been approved!')
        return redirect('adminpanel:trip_plans')
    
    return redirect('adminpanel:trip_plan_review', pk=pk)


@staff_and_group_required
def trip_plan_reject(request, pk):
    """Reject a trip plan with reason"""
    try:
        trip_plan = TripPlan.objects.get(pk=pk)
    except TripPlan.DoesNotExist:
        messages.warning(request, "This trip plan no longer exists.")
        return redirect('adminpanel:trip_plans')
    
    if request.method == 'POST':
        trip_plan.status = 'rejected'
        trip_plan.reviewed_by = request.user
        trip_plan.reviewed_at = timezone.now()
        trip_plan.admin_notes = request.POST.get('rejection_reason', 'Plan does not meet requirements.')
        trip_plan.save()
        
        # Notify customer
        Message.objects.create(
            user=trip_plan.user,
            category='trip_plans',
            subject=f'Your trip plan "{trip_plan.title}" requires revision',
            body=f'Your trip plan has been reviewed and requires some changes.\n\nReason: {trip_plan.admin_notes}\n\nPlease modify your plan and resubmit.'
        )
        
        messages.success(request, f'Trip plan "{trip_plan.title}" has been rejected with feedback.')
        return redirect('adminpanel:trip_plans')
    
    return redirect('adminpanel:trip_plan_review', pk=pk)


@staff_and_group_required
def trip_plan_edit(request, pk):
    """Admin edits trip plan and sends back to customer for review"""
    try:
        trip_plan = TripPlan.objects.get(pk=pk)
    except TripPlan.DoesNotExist:
        messages.warning(request, "This trip plan no longer exists.")
        return redirect('adminpanel:trip_plans')
    
    if request.method == 'POST':
        import json
        
        # Update trip plan fields
        trip_plan.title = request.POST.get('title', trip_plan.title)
        trip_plan.number_of_days = int(request.POST.get('number_of_days', trip_plan.number_of_days))
        trip_plan.budget = request.POST.get('budget') or trip_plan.budget
        trip_plan.travel_style = request.POST.get('travel_style', trip_plan.travel_style)
        trip_plan.accommodation = request.POST.get('accommodation', trip_plan.accommodation)
        trip_plan.transportation = request.POST.get('transportation', trip_plan.transportation)
        trip_plan.meals = request.POST.get('meals', trip_plan.meals)
        
        # Update itinerary if provided
        itinerary_json = request.POST.get('itinerary_json')
        if itinerary_json:
            try:
                trip_plan.itinerary = json.loads(itinerary_json)
            except:
                pass
        
        trip_plan.status = 'customer_review'
        trip_plan.reviewed_by = request.user
        trip_plan.reviewed_at = timezone.now()
        trip_plan.admin_notes = request.POST.get('admin_notes', 'We have made some adjustments to your trip plan.')
        trip_plan.save()
        
        # Notify customer
        Message.objects.create(
            user=trip_plan.user,
            category='trip_plans',
            subject=f'Your trip plan "{trip_plan.title}" has been updated',
            body=f'Our team has reviewed and updated your trip plan. Please review the changes and confirm.\n\nAdmin notes: {trip_plan.admin_notes}'
        )
        
        messages.success(request, f'Trip plan "{trip_plan.title}" has been updated and sent to customer for review.')
        return redirect('adminpanel:trip_plans')
    
    destinations = Destination.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'admin/trip_plan_edit.html', {
        'trip_plan': trip_plan,
        'all_destinations': destinations,
        'destinations_data': list(destinations.values('id', 'name', 'state', 'image', 'price_per_day'))
    })


@staff_and_group_required
def trip_plan_convert_package(request, pk):
    """Convert trip plan to a package (public or private)"""
    try:
        trip_plan = TripPlan.objects.get(pk=pk)
    except TripPlan.DoesNotExist:
        messages.warning(request, "This trip plan no longer exists.")
        return redirect('adminpanel:trip_plans')
    
    if request.method == 'POST':
        is_public = request.POST.get('is_public') == 'true'
        
        # Generate unique slug
        from django.utils.text import slugify
        base_slug = slugify(trip_plan.title)[:200]
        unique_slug = base_slug
        counter = 1
        while Package.objects.filter(url_name=unique_slug).exists():
            unique_slug = f"{base_slug}-{counter}"
            counter += 1

        # Create package from trip plan
        package = Package.objects.create(
            name=trip_plan.title,
            url_name=unique_slug,
            short_description=f"Curated {trip_plan.number_of_days}-day trip",
            description=f"A wonderful {trip_plan.number_of_days}-day journey created from customer planning.",
            category='family',  # Default, can be customized
            duration_days=trip_plan.number_of_days,
            duration_nights=max(0, trip_plan.number_of_days - 1),
            total_cost=trip_plan.budget or 0,
            accommodation_type=trip_plan.accommodation or 'hotel_3star',
            transportation_mode=trip_plan.transportation or 'car',
            meals_plan=trip_plan.meals or 'breakfast',
            itinerary=trip_plan.itinerary,
            is_preplanned=True,
            available_for_booking=True,
            is_custom=not is_public,  # If private, mark as custom
            is_active=True,
            created_by=request.user
        )
        
        # Add destinations
        package.destinations.set(trip_plan.destinations.all())
        
        # Link back to trip plan
        trip_plan.converted_to_package = package
        trip_plan.is_public = is_public
        trip_plan.save()
        
        # Notify customer
        if is_public:
            Message.objects.create(
                user=trip_plan.user,
                category='trip_plans',
                subject=f'Your trip plan "{trip_plan.title}" is now a public package!',
                body=f'Great news! Your amazing trip plan has been converted into a public package that other travelers can book. Thank you for your contribution!'
            )
            msg_type = 'public package available to all customers'
        else:
            Message.objects.create(
                user=trip_plan.user,
                category='trip_plans',
                subject=f'Your trip plan "{trip_plan.title}" is ready for booking!',
                body=f'Your trip plan has been converted into a private package. You can now proceed with booking!'
            )
            msg_type = 'private package for this customer only'
        
        messages.success(request, f'Trip plan converted to {msg_type}: "{package.name}"')
        return redirect('adminpanel:trip_plans')
    
    return render(request, 'admin/trip_plan_convert.html', {
        'trip_plan': trip_plan,
    })
