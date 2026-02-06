# adminpanel/permissions.py
from django.contrib.auth.models import Group

def is_owner(user):
    """Return True for owner group or superuser."""
    if not user or not user.is_active:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name='owner').exists()

def is_manager(user):
    """Return True for manager group or superuser."""
    if not user or not user.is_active:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name='manager').exists()

def is_admin_user(user):
    """
    Broad admin access: superuser OR staff OR in owner/manager groups.
    Use this for view protection.
    """
    if not user or not user.is_active:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return user.groups.filter(name__in=['owner', 'manager']).exists()
