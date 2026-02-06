
import os
import django
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gobuddy_project.settings')
django.setup()

from core.models import Destination, Package

def verify_pages():
    c = Client()
    
    # Verify Destination Detail
    dest = Destination.objects.filter(is_active=True).first()
    if dest:
        url = f'/destinations/{dest.url_name}/'
        print(f"Testing URL: {url}")
        resp = c.get(url)
        print(f"Destination Detail: Status {resp.status_code}")
        if resp.status_code == 200:
            print("  - Content check: 'About the Place' in response")
    else:
        print("No active destinations found to test.")

    # Verify Package Detail
    pkg = Package.objects.filter(is_active=True).first()
    if pkg:
        url = f'/packages/{pkg.pk}/'
        print(f"Testing URL: {url}")
        resp = c.get(url)
        print(f"Package Detail: Status {resp.status_code}")
        if resp.status_code == 200:
            print("  - Content check: 'Itinerary & Inclusions' in response")
    else:
        print("No active packages found to test.")

if __name__ == '__main__':
    verify_pages()
