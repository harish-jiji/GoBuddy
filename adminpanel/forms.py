from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group  # Added import
from .models import AdminNote, AdminConfiguration
from core.models import Package

User = get_user_model()

class AdminNoteForm(forms.ModelForm):
    class Meta:
        model = AdminNote
        fields = ['title', 'body', 'is_resolved']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500', 'placeholder': 'Note Title'}),
            'body': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500', 'rows': 4, 'placeholder': 'Write your note here...'}),
            'is_resolved': forms.CheckboxInput(attrs={'class': 'w-5 h-5 text-blue-600 rounded focus:ring-blue-500'}),
        }

class BookingFilterForm(forms.Form):
    status = forms.ChoiceField(
        choices=[('', 'All Statuses'), ('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'), ('completed', 'Completed')],
        required=False,
        widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'})
    )
    
    # We load users lazily or use a simple text search to avoid huge dropdowns
    user_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500', 'placeholder': 'Search by User Email/Name'})
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'})
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500'})
    )

class AdminConfigurationForm(forms.ModelForm):
    class Meta:
        model = AdminConfiguration
        fields = ['two_factor_code']
        widgets = {
            'two_factor_code': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Enter 6-digit code',
                'maxlength': '6'
            })
        }

class AdminCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500', 
        'placeholder': 'Password'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500', 
        'placeholder': 'Confirm Password'
    }))

    class Meta:
        model = User
        fields = ['email', 'full_name', 'phone']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500', 'placeholder': 'Email Address'}),
            'full_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500', 'placeholder': 'Full Name'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500', 'placeholder': 'Phone Number'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_staff = True
        user.is_active = True
        if commit:
            user.save()
            manager_group, _ = Group.objects.get_or_create(name='Manager')
            user.groups.add(manager_group)
        return user


class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = [
            'name', 'url_name', 'category', 'target_audience', 
            'duration_days', 'duration_nights', 'total_cost',
            'accommodation_type', 'transportation_mode', 'meals_plan',
            'short_description', 'description', 'is_active', 
            'is_preplanned', 'available_for_booking'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind classes to all fields
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = f'{current_classes} h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs['class'] = f'{current_classes} space-y-2'
            else:
                field.widget.attrs['class'] = f'{current_classes} w-full px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors'
