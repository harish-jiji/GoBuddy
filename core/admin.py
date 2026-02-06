from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import GoUser, Destination, Package, Booking, BookingTraveler, Message, AdminUser

# Custom User Admin
class GoUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'full_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone', 'profile_image', 'date_of_birth', 'location', 'bio')}),
        ('Preferences', {'fields': ('travel_style', 'accommodation_preference', 'budget_range', 'travel_companions', 'travel_interests')}),
        ('Notifications', {'fields': ('email_notifications', 'booking_updates', 'payment_alerts', 'special_offers')}),
        ('Privacy', {'fields': ('public_profile', 'show_travel_history', 'data_analytics', 'two_factor_enabled')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password_1', 'password_2'),
        }),
    )

# admin.site.register(GoUser, GoUserAdmin) # Hidden as per user request

# Admin User Proxy Registration
from django import forms

class AdminUserCreationForm(forms.ModelForm):
    password_1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        strip=False,
    )
    password_2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        strip=False,
    )

    class Meta:
        model = AdminUser
        fields = ("email", "full_name")

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password_1")
        p2 = cleaned_data.get("password_2")
        if p1 and p2 and p1 != p2:
            self.add_error("password_2", "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password_1"])
        if commit:
            user.save()
        return user

@admin.register(AdminUser)
class AdminUserAdmin(UserAdmin):
    add_form = AdminUserCreationForm
    
    list_display = ('email', 'full_name', 'is_staff', 'is_superuser', 'last_login')
    list_filter = ('is_superuser', 'is_active')
    search_fields = ('email', 'full_name')
    ordering = ('email',)
    
    # Correct fieldsets for Email-based user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password_1', 'password_2'), 
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True)

    def save_model(self, request, obj, form, change):
        obj.is_staff = True
        obj.save()
        # Assign to Manager Group
        from django.contrib.auth.models import Group
        manager_group, _ = Group.objects.get_or_create(name='Manager')
        obj.groups.add(manager_group)

@admin.register(Destination)
class DestinationAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'is_active')
    search_fields = ('name', 'country', 'description')
    list_filter = ('is_active', 'country')

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'total_cost', 'duration_days', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'category')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'package', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'package__name', 'booking_reference')

@admin.register(BookingTraveler)
class BookingTravelerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'booking', 'age', 'passport_no', 'phone')
    search_fields = ('full_name', 'booking__booking_reference')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'subject', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at', 'category')
    search_fields = ('subject', 'body', 'user__email')
