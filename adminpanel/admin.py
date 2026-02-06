from django.contrib import admin
from .models import AdminNote, AdminConfiguration

@admin.register(AdminNote)
class AdminNoteAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'booking', 'package', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at')
    search_fields = ('title', 'body', 'author__email')

@admin.register(AdminConfiguration)
class AdminConfigurationAdmin(admin.ModelAdmin):
    list_display = ('two_factor_code', 'last_updated', 'updated_by')
    # Prevent creating multiple configs from admin if one exists (optional UI enforcement)
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)
