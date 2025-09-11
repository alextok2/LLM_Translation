from rest_framework.permissions import BasePermission

def in_group(user, group_name: str) -> bool:
    if not user.is_authenticated:
        return False
    if group_name == "admin":
        return user.is_superuser or user.is_staff or user.groups.filter(name="admin").exists()
    return user.groups.filter(name=group_name).exists()

def is_admin_user(user) -> bool:
    return user.is_authenticated and (user.is_superuser or user.is_staff or user.groups.filter(name="admin").exists())

class IsAdminGroup(BasePermission):
    def has_permission(self, request, view):
        return is_admin_user(request.user)

class IsTranslatorGroup(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return u.is_authenticated and (u.groups.filter(name="translator").exists() or is_admin_user(u))