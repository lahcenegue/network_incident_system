from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('users/', views.UserManagementView.as_view(), name='users'),
    path('settings/', views.SystemSettingsView.as_view(), name='settings'),
]