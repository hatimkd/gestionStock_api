
# utils.py - Helper functions for role management
from django.contrib.auth.models import Group, User

def assign_user_to_group(user, group_name):
    """Assign user to a group (role)"""
    group, created = Group.objects.get_or_create(name=group_name)
    user.groups.add(group)
    user.save()

def remove_user_from_group(user, group_name):
    """Remove user from a group (role)"""
    try:
        group = Group.objects.get(name=group_name)
        user.groups.remove(group)
        user.save()
    except Group.DoesNotExist:
        pass

def get_user_roles(user):
    """Get all roles (groups) for a user"""
    return [group.name for group in user.groups.all()]

def has_role(user, role_name):
    """Check if user has a specific role"""
    return user.groups.filter(name=role_name).exists()