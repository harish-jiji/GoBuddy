from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [

    # Dashboard
    path('dashboard/', views.dashboard, name='US_Dashboard'),

    # Bookings
    path('bookings/', views.bookings_view, name='bookings'),
    path('booking/<int:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),

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
    path('inbox/message/<int:message_id>/', views.message_detail, name='message_detail'),
    path('inbox/message/<int:message_id>/delete/', views.delete_message, name='delete_message'),

    # Profile & Settings
    path('profile/', views.profile, name='profile'),
    path('profile/security/', views.security_settings, name='security_settings'),
    path('profile/privacy/', views.privacy_settings, name='privacy_settings'),
    path('profile/notifications/', views.notification_settings, name='notification_settings'),

    # Friends System
    path('friends/', views.friends_list, name='friends_list'),
    path('friends/search/', views.search_friends, name='search_friends'),
    path('friends/request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friends/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friends/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),

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
    
    # Payment Flow
    path('booking/<int:booking_id>/pay/', views.initiate_payment, name='initiate_payment'),
    path('booking/<int:booking_id>/pay/send-otp/', views.send_payment_otp, name='send_payment_otp'),
    path('booking/<int:booking_id>/pay/verify-otp/', views.verify_payment_otp, name='verify_payment_otp'),
    path('payments/', views.payments_list, name='payments_list'),
]
