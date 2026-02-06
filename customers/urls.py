from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [

    # Dashboard
    path('dashboard/', views.dashboard, name='US_Dashboard'),

    # Bookings
    path('bookings/', views.bookings_view, name='bookings'),

    # Destinations
    path('destinations/', views.destinations_list, name='destinations_list'),
    path('destination/<slug:url_name>/', views.destination_detail, name='destination_detail'),

    # Trip Planner (Single Page)
    path('plan-trips/', views.plan_trip_itinerary, name='plan_trips'),
    path('plan-trips/save/', views.save_trip, name='save_trip'),

    # Trip Operations
    path('trip/<int:trip_id>/', views.trip_detail, name='trip_detail'),
    path('trip/<int:trip_id>/edit/', views.edit_trip, name='edit_trip'),
    path('trip/<int:trip_id>/delete/', views.delete_trip, name='delete_trip'),
    path('trip/<int:trip_id>/convert/', views.convert_trip, name='convert_trip'),

    # Inbox
    path('inbox/', views.inbox, name='inbox'),

    # Profile
    path('profile/', views.profile, name='profile'),

    # Trip Management
    path('my-trips/', views.my_trips, name='my_trips'),
    path('trip/<int:trip_id>/submit/', views.submit_for_approval, name='submit_for_approval'),
    path('trip/<int:trip_id>/accept-revision/', views.accept_admin_revision, name='accept_admin_revision'),
    path('trip/<int:trip_id>/reject-revision/', views.reject_admin_revision, name='reject_admin_revision'),
    path('trip/<int:trip_id>/select-dates/', views.select_trip_dates, name='select_trip_dates'),

    # Browse and Book Packages
    path('packages/', views.browse_packages, name='browse_packages'),
    path('package/<int:package_id>/', views.package_detail_view, name='package_detail'),
    path('package/<int:package_id>/book/', views.book_package, name='book_package'),
]
