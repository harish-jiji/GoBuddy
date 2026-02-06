from django import forms
from core.models import Package

class PackageForm(forms.ModelForm):
    class Meta:
        model = Package
        fields = [
            'name', 'url_name', 'category', 'destinations',
            'duration_days', 'duration_nights', 'total_cost',
            'accommodation_type', 'transportation_mode', 'meals_plan',
            'short_description', 'description', 'is_active'
        ]
        widgets = {
            'destinations': forms.CheckboxSelectMultiple(),
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
