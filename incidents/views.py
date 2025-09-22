from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class BaseIncidentView(LoginRequiredMixin, TemplateView):
    """Base view for all incident-related pages"""
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context

# Transport Networks Views
class TransportListView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Transport Networks - View Incidents'
        context['network_type'] = 'Transport Networks'
        return context

class TransportCreateView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Transport Networks - Add New Incident'
        context['network_type'] = 'Transport Networks'
        return context

class TransportHistoricalView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Transport Networks - Historical Incidents'
        context['network_type'] = 'Transport Networks'
        return context

# File Access Networks Views
class FileAccessListView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'File Access Networks - View Incidents'
        context['network_type'] = 'File Access Networks'
        return context

class FileAccessCreateView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'File Access Networks - Add New Incident'
        context['network_type'] = 'File Access Networks'
        return context

class FileAccessHistoricalView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'File Access Networks - Historical Incidents'
        context['network_type'] = 'File Access Networks'
        return context

# Radio Access Networks Views
class RadioAccessListView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Radio Access Networks - View Incidents'
        context['network_type'] = 'Radio Access Networks'
        return context

class RadioAccessCreateView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Radio Access Networks - Add New Incident'
        context['network_type'] = 'Radio Access Networks'
        return context

class RadioAccessHistoricalView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Radio Access Networks - Historical Incidents'
        context['network_type'] = 'Radio Access Networks'
        return context

# Core Networks Views
class CoreListView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Core Networks - View Incidents'
        context['network_type'] = 'Core Networks'
        return context

class CoreCreateView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Core Networks - Add New Incident'
        context['network_type'] = 'Core Networks'
        return context

class CoreHistoricalView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Core Networks - Historical Incidents'
        context['network_type'] = 'Core Networks'
        return context

# Backbone Internet Networks Views
class BackboneListView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Backbone Internet Networks - View Incidents'
        context['network_type'] = 'Backbone Internet Networks'
        return context

class BackboneCreateView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Backbone Internet Networks - Add New Incident'
        context['network_type'] = 'Backbone Internet Networks'
        return context

class BackboneHistoricalView(BaseIncidentView):
    template_name = 'base/placeholder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Backbone Internet Networks - Historical Incidents'
        context['network_type'] = 'Backbone Internet Networks'
        return context