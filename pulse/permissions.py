from rest_framework.permissions import BasePermission

from .models import UserProfile


class IsAdminUser(BasePermission):
    """Allow access only when request.user.profile.role == ADMIN."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        try:
            return user.profile.role == UserProfile.Role.ADMIN
        except UserProfile.DoesNotExist:
            return False
