# core/urls.py
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Home page
    path('', views.home, name='home'),

    # Destination pages
    path('destinations/<slug:url_name>/', views.destination_detail, name='destination_detail'),

    # Packages pages
    path('packages/', views.packages_view, name='packages'),
    path('destinations/', views.destinations, name='destinations'),
    path('packages/<int:pk>/', views.package_detail, name='package_detail'),

    # Authentication
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.signout, name='logout'),

    # Password Recovery (Security Questions)
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-questions/', views.verify_security_questions, name='verify_security_questions'),
    path('reset-password/', views.reset_password, name='reset_password'),
]
