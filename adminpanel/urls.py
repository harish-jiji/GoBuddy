# adminpanel/urls.py
from django.urls import path
from django.views.generic import TemplateView
from . import views

app_name = 'adminpanel'

urlpatterns = [
    # Login
    path('login/', views.manager_login, name='manager_login'),

    path('dashboard/', views.dashboard, name='dashboard'),

    # destinations CRUD
    path('destinations/', views.DestinationListView.as_view(), name='destinations'),
    path('destinations/add/', views.DestinationCreateView.as_view(), name='destination_add'),
    path('destinations/<int:pk>/edit/', views.DestinationUpdateView.as_view(), name='destination_edit'),
    path('destinations/<int:pk>/delete/', views.DestinationDeleteView.as_view(), name='destination_delete'),

    # packages
    # packages
    path('packages/', views.PackageListView.as_view(), name='packages'),
    path('packages/add/', views.PackageCreateView.as_view(), name='package_add'),
    path('packages/<int:pk>/', views.package_detail, name='package_detail'),
    path('packages/<int:pk>/edit/', views.PackageUpdateView.as_view(), name='package_edit'),
    path('packages/<int:pk>/delete/', views.PackageDeleteView.as_view(), name='package_delete'),

    # bookings
    path('bookings/', views.BookingListView.as_view(), name='bookings'),
    path('bookings/<int:pk>/', views.BookingDetailView.as_view(), name='booking_detail'),
    path('bookings/<int:pk>/approve/', views.booking_approve, name='booking_approve'),
    path('bookings/<int:pk>/reject/', views.booking_reject, name='booking_reject'),
    path('bookings/export/csv/', views.export_bookings_csv, name='export_bookings_csv'),

    # users
    path('users/', views.users_list, name='users'),
    path('users/add-admin/', views.AdminCreateView.as_view(), name='user_add_admin'),

    # analytics & expenses
    path('analytics/', views.analytics, name='analytics'),
    path('expenses/', views.expenses_list, name='expenses'),

    # settings (template placeholders)
    path('settings/billing/', TemplateView.as_view(template_name='admin/settings/billing.html'), name='settings_billing'),
    path('settings/email/', TemplateView.as_view(template_name='admin/settings/email.html'), name='settings_email'),
    path('settings/notifications/', TemplateView.as_view(template_name='admin/settings/notifications.html'), name='settings_notifications'),
    path('settings/security/', views.security_settings, name='settings_security'),

    # trip plans
    path('trip-plans/', views.trip_plans_list, name='trip_plans'),
    path('trip-plans/<int:pk>/', views.trip_plan_review, name='trip_plan_review'),
    path('trip-plans/<int:pk>/approve/', views.trip_plan_approve, name='trip_plan_approve'),
    path('trip-plans/<int:pk>/reject/', views.trip_plan_reject, name='trip_plan_reject'),
    path('trip-plans/<int:pk>/edit/', views.trip_plan_edit, name='trip_plan_edit'),
    path('trip-plans/<int:pk>/convert-package/', views.trip_plan_convert_package, name='trip_plan_convert_package'),
]
