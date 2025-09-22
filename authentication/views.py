from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from .models import CustomUser
from .forms import CustomAuthenticationForm

class LoginView(auth_views.LoginView):
    template_name = 'authentication/login.html'
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        # Log IP address on successful login
        user = form.get_user()
        user.last_login_ip = self.get_client_ip()
        user.save(update_fields=['last_login_ip'])
        
        messages.success(self.request, f'Welcome back, {user.first_name or user.username}!')
        return super().form_valid(form)
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

class LogoutView(auth_views.LogoutView):
    next_page = '/auth/login/'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'authentication/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context