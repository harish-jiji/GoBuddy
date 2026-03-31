from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

User = settings.AUTH_USER_MODEL


# ============================================================
# USER PROFILE MODEL (UPDATED & CLEANED)
# ============================================================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # BASIC INFO
    phone = models.CharField(max_length=30, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # TRAVEL STYLE
    TRAVEL_STYLE_CHOICES = [
        ('budget', 'Budget Traveler'),
        ('comfort', 'Comfort Seeker'),
        ('luxury', 'Luxury Traveler'),
    ]
    travel_style = models.CharField(max_length=20, choices=TRAVEL_STYLE_CHOICES, blank=True, null=True)

    # ACCOMMODATION PREF
    ACCOMMODATION_CHOICES = [
        ('hotel', 'Hotels'),
        ('resort', 'Resorts'),
        ('homestay', 'Homestays'),
        ('hostel', 'Hostels'),
    ]
    accommodation_preference = models.CharField(max_length=20, choices=ACCOMMODATION_CHOICES, blank=True, null=True)

    # BUDGET RANGE
    BUDGET_RANGE_CHOICES = [
        ('low', '₹10K - ₹25K'),
        ('medium', '₹25K - ₹50K'),
        ('high', '₹50K - ₹1L'),
        ('premium', '₹1L+'),
    ]
    budget_range = models.CharField(max_length=20, choices=BUDGET_RANGE_CHOICES, blank=True, null=True)

    # TRAVEL COMPANIONS
    COMPANIONS_CHOICES = [
        ('solo', 'Solo'),
        ('couple', 'Couple'),
        ('family', 'Family'),
        ('friends', 'Friends'),
        ('group', 'Group'),
    ]
    travel_companions = models.CharField(max_length=20, choices=COMPANIONS_CHOICES, blank=True, null=True)

    # INTERESTS (JSON list)
    travel_interests = models.JSONField(blank=True, null=True, default=list)

    # NOTIFICATION SETTINGS
    email_notifications = models.BooleanField(default=True)
    booking_updates = models.BooleanField(default=True)
    payment_alerts = models.BooleanField(default=True)
    special_offers = models.BooleanField(default=True)

    # PRIVACY
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('friends', 'Friends Only'),
    ]
    privacy_level = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='public')

    # SECURITY QUESTIONS
    security_q1 = models.CharField(max_length=255, blank=True, null=True)
    security_a1 = models.CharField(max_length=255, blank=True, null=True)
    security_q2 = models.CharField(max_length=255, blank=True, null=True)
    security_a2 = models.CharField(max_length=255, blank=True, null=True)
    security_q3 = models.CharField(max_length=255, blank=True, null=True)
    security_a3 = models.CharField(max_length=255, blank=True, null=True)

    # PROFILE PROGRESS
    profile_completion_percentage = models.IntegerField(default=0)
    profile_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} Profile"

    # Helper: Convert JSON list to Python list
    @property
    def get_travel_interests_list(self):
        return self.travel_interests if isinstance(self.travel_interests, list) else []


# AUTO-CREATE PROFILE FOR NEW USER
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()
# ============================================================
# FRIENDSHIP MODEL
# ============================================================
class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friend_requests')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friend_requests')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.email} -> {self.to_user.email} ({self.status})"


# ============================================================
# TRIP PLAN MODEL (Enhanced with Approval Workflow)
# ============================================================
class TripPlan(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
        ('customer_review', 'Customer Reviewing Changes'),
    ]

    TRAVEL_STYLE_CHOICES = [
        ('budget', 'Budget Friendly'),
        ('comfort', 'Comfort'),
        ('luxury', 'Luxury'),
    ]

    TRANSPORTATION_CHOICES = [
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

    ACCOMMODATION_CHOICES = [
        ('hotel_3star', '3 Star Hotel'),
        ('hotel_4star', '4 Star Hotel'),
        ('hotel_5star', '5 Star Hotel'),
        ('resort', 'Resort'),
        ('homestay', 'Homestay'),
        ('villa', 'Private Villa'),
        ('hostel', 'Hostel'),
    ]

    start_location = models.CharField(max_length=255, blank=True, null=True, help_text="Starting point of the trip")
    end_location = models.CharField(max_length=255, blank=True, null=True, help_text="Ending point of the trip")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_plans')
    
    # Multiple destinations support
    destinations = models.ManyToManyField('core.Destination', related_name='trip_plans', blank=True)
    # Keep single destination for backward compatibility
    destination = models.ForeignKey('core.Destination', on_delete=models.SET_NULL, null=True, blank=True, related_name='old_trip_plans')

    title = models.CharField(max_length=255, blank=True, null=True)

    # Trip duration
    number_of_days = models.PositiveSmallIntegerField(default=1, help_text="Number of days for the trip")
    start_date = models.DateField(null=True, blank=True, help_text="Selected after plan approval")
    end_date = models.DateField(null=True, blank=True)

    travelers = models.PositiveSmallIntegerField(default=1)

    # Travel preferences
    travel_style = models.CharField(max_length=50, choices=TRAVEL_STYLE_CHOICES, blank=True, null=True)
    accommodation = models.CharField(max_length=50, choices=ACCOMMODATION_CHOICES, blank=True, null=True)
    transportation = models.CharField(max_length=50, choices=TRANSPORTATION_CHOICES, blank=True, null=True)
    meals = models.CharField(max_length=50, choices=MEAL_CHOICES, blank=True, null=True)

    budget = models.PositiveIntegerField(null=True, blank=True)

    interests = models.JSONField(default=list, blank=True)
    
    # Enhanced itinerary with day-by-day planning
    itinerary = models.JSONField(default=list, blank=True, help_text="Array of day objects with activities and destinations")

    notes = models.TextField(blank=True, null=True)

    # Approval workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    admin_notes = models.TextField(blank=True, null=True, help_text="Admin feedback or revision notes")
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_trip_plans')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    # Package conversion
    converted_to_package = models.ForeignKey('core.Package', on_delete=models.SET_NULL, null=True, blank=True, related_name='source_trip_plan')
    is_public = models.BooleanField(default=False, help_text="If true, admin can make this plan available for all customers")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"TripPlan {self.id} - {self.title or 'Untitled'}"

    def get_destinations_display(self):
        """Get display string for multiple destinations"""
        dests = list(self.destinations.all())
        if self.destination and self.destination not in dests:
            dests.append(self.destination)
        return ", ".join([d.name for d in dests if d])
