# adminpanel/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class AdminNote(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255)
    body = models.TextField()

    # Link to core app models
    # We use string references to avoid circular imports at module level
    booking = models.ForeignKey(
        'core.Booking',
        null=True,
        blank=True,
        related_name='admin_notes',
        on_delete=models.CASCADE
    )
    package = models.ForeignKey(
        'core.Package',
        null=True,
        blank=True,
        related_name='admin_notes',
        on_delete=models.CASCADE
    )

    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class AdminConfiguration(models.Model):
    # Singleton model to store global admin settings
    two_factor_code = models.CharField(max_length=6, default='123456', help_text="Global 6-digit access code for admins")
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and AdminConfiguration.objects.exists():
            # If trying to create a new one, update the existing one instead? 
            # Or just raise error. For simplicity, we just enforce ID=1
            self.pk = 1
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Global Admin Config (Code: {self.two_factor_code})"
