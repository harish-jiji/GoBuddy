from django.contrib import admin
from .models import UserProfile, TripPlan

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'profile_completed', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'phone')
    list_filter = ('profile_completed', 'created_at')

@admin.register(TripPlan)
class TripPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'destination', 'start_date', 'travelers')
    search_fields = ('title', 'user__email', 'notes')
    list_filter = ('start_date', 'created_at')
