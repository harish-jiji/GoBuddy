# core/models.py

from django.db import models
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager, PermissionsMixin)
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
import uuid


# ======================================================
# CUSTOM USER MANAGER
# ======================================================
class GoUserManager(BaseUserManager):
    def create_user(self, email, password=None, full_name=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name or "",
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, full_name=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, full_name, **extra_fields)


# ======================================================
# CUSTOM USER MODEL
# ======================================================
class GoUser(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True, max_length=255)
    phone = models.CharField(max_length=30, blank=True, null=True)
    profile_image = models.URLField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    TRAVEL_STYLE_CHOICES = [
        ('budget', 'Budget Traveler'),
        ('comfort', 'Comfort Seeker'),
        ('luxury', 'Luxury Traveler'),
    ]
    travel_style = models.CharField(max_length=20, choices=TRAVEL_STYLE_CHOICES, blank=True, null=True)

    ACCOMMODATION_CHOICES = [
        ('hotel', 'Hotels'),
        ('resort', 'Resorts'),
        ('homestay', 'Homestays'),
        ('hostel', 'Hostels'),
    ]
    accommodation_preference = models.CharField(max_length=20, choices=ACCOMMODATION_CHOICES, blank=True, null=True)

    BUDGET_RANGE_CHOICES = [
        ('low', '₹10K - ₹25K'),
        ('medium', '₹25K - ₹50K'),
        ('high', '₹50K - ₹1L'),
        ('premium', '₹1L+'),
    ]
    budget_range = models.CharField(max_length=20, choices=BUDGET_RANGE_CHOICES, blank=True, null=True)

    travel_companions = models.CharField(max_length=20, blank=True, null=True)
    travel_interests = models.JSONField(blank=True, null=True, default=list)

    email_notifications = models.BooleanField(default=True)
    booking_updates = models.BooleanField(default=True)
    payment_alerts = models.BooleanField(default=True)
    special_offers = models.BooleanField(default=False)

    public_profile = models.BooleanField(default=True)
    show_travel_history = models.BooleanField(default=True)
    data_analytics = models.BooleanField(default=True)
    two_factor_enabled = models.BooleanField(default=False)

    profile_completed = models.BooleanField(default=False)
    profile_completion_percentage = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = GoUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    def calculate_profile_completion(self):
        required = [
            'full_name', 'email', 'phone',
            'date_of_birth', 'location', 'bio',
            'profile_image'
        ]
        optional = [
            'travel_style', 'accommodation_preference',
            'budget_range', 'travel_companions',
            'travel_interests'
        ]

        completed_required = sum(1 for f in required if getattr(self, f))
        completed_optional = sum(1 for f in optional if getattr(self, f))

        required_score = (completed_required / len(required)) * 60
        optional_score = (completed_optional / len(optional)) * 40

        percent = int(required_score + optional_score)
        self.profile_completion_percentage = percent
        self.profile_completed = percent >= 80

        return percent

    def save(self, *args, **kwargs):
        self.calculate_profile_completion()
        super().save(*args, **kwargs)


class AdminUser(GoUser):
    class Meta:
        proxy = True
        verbose_name = 'Admin User'
        verbose_name_plural = 'Admin Users'


# ======================================================
# DESTINATION MODEL
# ======================================================
class Destination(models.Model):
    INDIAN_STATES = [
        ('AN', 'Andaman and Nicobar Islands'),
        ('AP', 'Andhra Pradesh'),
        ('AR', 'Arunachal Pradesh'),
        ('AS', 'Assam'),
        ('BR', 'Bihar'),
        ('CH', 'Chandigarh'),
        ('CT', 'Chhattisgarh'),
        ('DN', 'Dadra and Nagar Haveli and Daman and Diu'),
        ('DL', 'Delhi'),
        ('GA', 'Goa'),
        ('GJ', 'Gujarat'),
        ('HR', 'Haryana'),
        ('HP', 'Himachal Pradesh'),
        ('JK', 'Jammu and Kashmir'),
        ('JH', 'Jharkhand'),
        ('KA', 'Karnataka'),
        ('KL', 'Kerala'),
        ('LA', 'Ladakh'),
        ('LD', 'Lakshadweep'),
        ('MP', 'Madhya Pradesh'),
        ('MH', 'Maharashtra'),
        ('MN', 'Manipur'),
        ('ML', 'Meghalaya'),
        ('MZ', 'Mizoram'),
        ('NL', 'Nagaland'),
        ('OR', 'Odisha'),
        ('PY', 'Puducherry'),
        ('PB', 'Punjab'),
        ('RJ', 'Rajasthan'),
        ('SK', 'Sikkim'),
        ('TN', 'Tamil Nadu'),
        ('TG', 'Telangana'),
        ('TR', 'Tripura'),
        ('UP', 'Uttar Pradesh'),
        ('UK', 'Uttarakhand'),
        ('WB', 'West Bengal'),
    ]

    name = models.CharField(max_length=150)
    country = models.CharField(max_length=100, blank=True, default='India')
    state = models.CharField(max_length=5, choices=INDIAN_STATES, blank=True, null=True)
    url_name = models.SlugField(max_length=180, unique=True, blank=True, verbose_name="URL Name (Slug)")
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='destinations/', blank=True, null=True)
    price_per_day = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    best_season = models.CharField(max_length=100, blank=True)
    # Location coordinates for Google Maps distance calculation
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Latitude for distance calculations")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text="Longitude for distance calculations")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.url_name:
            self.url_name = slugify(self.name)[:180]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ======================================================
# PACKAGE MODEL (FINAL, SINGLE, CORRECT)
# ======================================================
class Package(models.Model):
    PACKAGE_CATEGORY_CHOICES = [
        ('honeymoon', 'Honeymoon'),
        ('family', 'Family'),
        ('solo', 'Solo'),
        ('friends', 'Friends'),
    ]

    ACCOMMODATION_CHOICES = [
        ('hotel_3star', '3 Star Hotel'),
        ('hotel_4star', '4 Star Hotel'),
        ('hotel_5star', '5 Star Hotel'),
        ('resort', 'Resort'),
        ('homestay', 'Homestay'),
        ('villa', 'Private Villa'),
    ]

    TRANSPORT_CHOICES = [
        ('flight', 'Flight'),
        ('train', 'Train'),
        ('bus', 'Bus (AC Volvo)'),
        ('car', 'Private Car'),
        ('mixed', 'Mixed Mode'),
    ]

    MEAL_CHOICES = [
        ('breakfast', 'Breakfast Only'),
        ('breakfast_dinner', 'Breakfast & Dinner'),
        ('all_meals', 'All Meals'),
        ('no_meals', 'No Meals'),
    ]

    name = models.CharField(max_length=255)
    url_name = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="URL Name (Slug)")
    short_description = models.TextField(blank=True, help_text="Brief summary for cards")
    description = models.TextField(blank=True, help_text="Detailed itinerary and inclusions")
    
    # Relationships
    destinations = models.ManyToManyField(Destination, related_name='packages', blank=True)
    
    category = models.CharField(max_length=20, choices=PACKAGE_CATEGORY_CHOICES, default='family')

    TARGET_AUDIENCE_CHOICES = [
        ('single', 'Single'),
        ('couple', 'Couples'),
        ('family', 'Family'),
        ('friends', 'Friends'),
    ]
    target_audience = models.CharField(max_length=20, choices=TARGET_AUDIENCE_CHOICES, default='family', help_text="Recommended audience for this package")

    # Core Details
    duration_days = models.PositiveIntegerField(default=1)
    duration_nights = models.PositiveIntegerField(default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Inclusions
    accommodation_type = models.CharField(max_length=20, choices=ACCOMMODATION_CHOICES, default='hotel_3star')
    transportation_mode = models.CharField(max_length=20, choices=TRANSPORT_CHOICES, default='car')
    meals_plan = models.CharField(max_length=20, choices=MEAL_CHOICES, default='breakfast')
    
    # Day-by-day itinerary (same structure as TripPlan for consistency)
    itinerary = models.JSONField(default=list, blank=True, help_text="Day-by-day itinerary with places and activities")
    
    # Package type flags
    is_preplanned = models.BooleanField(default=False, help_text="Admin-created pre-planned package")
    available_for_booking = models.BooleanField(default=True, help_text="Enable/disable customer booking")
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_packages')

    is_custom = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.url_name:
            self.url_name = slugify(self.name)[:255]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def get_destinations_display(self):
        """Get display string for multiple destinations"""
        return ", ".join([d.name for d in self.destinations.all()])


# ======================================================
# BOOKING MODEL
# ======================================================
class Booking(models.Model):
    BOOKING_STATUS = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, blank=True)

    booking_reference = models.CharField(max_length=120, unique=True, blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=30, choices=BOOKING_STATUS, default='pending')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = f"GB-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.booking_reference} - {self.user.email}"


class BookingTraveler(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='travelers')
    full_name = models.CharField(max_length=150)
    age = models.PositiveIntegerField(null=True, blank=True)
    passport_no = models.CharField(max_length=80, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.booking.booking_reference})"


# ======================================================
# USER MESSAGES
# ======================================================
class Message(models.Model):
    CATEGORY_CHOICES = [
        ('bookings', 'Bookings'),
        ('payments', 'Payments'),
        ('offers', 'Offers'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='system')
    subject = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email}: {self.subject}"
