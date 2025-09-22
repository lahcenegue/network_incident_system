from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied

class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure only admin users can access admin panel"""
    login_url = '/auth/login/'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_admin():
            raise PermissionDenied("Admin access required.")
        return super().dispatch(request, *args, **kwargs)

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Admin Panel - Dashboard'
        return context

class UserManagementView(AdminRequiredMixin, TemplateView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Admin Panel - User Management'
        return context

class SystemSettingsView(AdminRequiredMixin, TemplateView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Admin Panel - System Settings'
        return context