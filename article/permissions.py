




# permissions.py
from rest_framework.permissions import BasePermission

class IsGestionnaire(BasePermission):
    """
    Autorise l'accès uniquement aux utilisateurs appartenant au groupe 'gestionnaire'.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.groups.filter(name='gestionnaire').exists() or
            request.user.groups.filter(name='admin').exists()
        )
