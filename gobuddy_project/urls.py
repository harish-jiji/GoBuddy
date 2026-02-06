# gobuddy_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django default admin
    path('adminpanel/', include('adminpanel.urls', namespace='adminpanel')),
    path('admin/', admin.site.urls),
    
    # Core app (Homepage, Destinations, Packages, Auth)
    path('', include(('core.urls', 'core'), namespace='core')),

    # Customers dashboard + customer routes
    path('customers/', include(('customers.urls', 'customers'), namespace='customers')),

    # Admin panel (tourism managers)
    path('panel/', include(('adminpanel.urls', 'adminpanel'), namespace='adminpanel')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
