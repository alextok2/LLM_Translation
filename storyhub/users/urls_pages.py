from django.urls import path
from .views_pages import RoleSettingsView, UserDashboardView

urlpatterns = [
    path("account/roles/", RoleSettingsView.as_view(), name="role_settings"),
    path("account/", UserDashboardView.as_view(), name="user_account"),
]