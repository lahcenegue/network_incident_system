# Replace your incidents/services.py file with this corrected version

from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone
from .models import (
    TransportNetworkIncident, FileAccessNetworkIncident,
    RadioAccessNetworkIncident, CoreNetworkIncident,
    BackboneInternetNetworkIncident
)


class IncidentSearchService:
    """Service class for handling incident search and filtering"""
    
    def __init__(self, model_class):
        self.model_class = model_class
    
    def search_incidents(self, search_form_data):
        """
        Main search method that applies all filters and returns QuerySet
        """
        queryset = self.model_class.objects.select_related('created_by', 'updated_by')
        
        # Apply text search
        if search_form_data.get('search_query'):
            queryset = self._apply_text_search(queryset, search_form_data['search_query'])
        
        # Apply date range filters
        if search_form_data.get('date_from'):
            queryset = queryset.filter(date_time_incident__gte=search_form_data['date_from'])
        
        if search_form_data.get('date_to'):
            queryset = queryset.filter(date_time_incident__lte=search_form_data['date_to'])
        
        # Apply status filter
        if search_form_data.get('status'):
            queryset = self._apply_status_filter(queryset, search_form_data['status'])
        
        # Apply cause and origin filters
        if search_form_data.get('cause'):
            queryset = queryset.filter(cause=search_form_data['cause'])
        
        if search_form_data.get('origin'):
            queryset = queryset.filter(origin=search_form_data['origin'])
        
        # Apply network-specific filters
        queryset = self._apply_network_specific_filters(queryset, search_form_data)
        
        # Apply sorting
        sort_by = search_form_data.get('sort_by', '-date_time_incident')
        queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def _apply_text_search(self, queryset, search_query):
        """Apply text search across relevant fields"""
        search_query = search_query.strip()
        
        if not search_query:
            return queryset
        
        # Base fields common to all incidents
        q_objects = Q()
        q_objects |= Q(id__icontains=search_query)
        q_objects |= Q(cause__icontains=search_query)
        q_objects |= Q(origin__icontains=search_query)
        q_objects |= Q(impact_comment__icontains=search_query)
        q_objects |= Q(created_by__username__icontains=search_query)
        
        # Network-specific search fields - CORRECTED field names
        if self.model_class == TransportNetworkIncident:
            q_objects |= Q(region_loop__icontains=search_query)
            q_objects |= Q(system_capacity__icontains=search_query)
            q_objects |= Q(extremity_a__icontains=search_query)
            q_objects |= Q(extremity_b__icontains=search_query)
        
        elif self.model_class == FileAccessNetworkIncident:
            q_objects |= Q(do_wilaya__icontains=search_query)  # CORRECTED: do_wilaya not wilaya
            q_objects |= Q(zone_metro__icontains=search_query)
            q_objects |= Q(site__icontains=search_query)
            q_objects |= Q(ip_address__icontains=search_query)
        
        elif self.model_class == RadioAccessNetworkIncident:
            q_objects |= Q(do_wilaya__icontains=search_query)  # CORRECTED: do_wilaya not wilaya
            q_objects |= Q(site__icontains=search_query)
            q_objects |= Q(ip_address__icontains=search_query)
        
        elif self.model_class == CoreNetworkIncident:
            q_objects |= Q(platform__icontains=search_query)
            q_objects |= Q(region_node__icontains=search_query)
            q_objects |= Q(site__icontains=search_query)
            q_objects |= Q(extremity_a__icontains=search_query)
            q_objects |= Q(extremity_b__icontains=search_query)
        
        elif self.model_class == BackboneInternetNetworkIncident:
            q_objects |= Q(interconnect_type__icontains=search_query)
            q_objects |= Q(platform_igw__icontains=search_query)
            q_objects |= Q(link_label__icontains=search_query)
        
        return queryset.filter(q_objects)
    
    def _apply_status_filter(self, queryset, status):
        """Apply status-based filtering"""
        now = timezone.now()
        
        if status == 'active':
            return queryset.filter(date_time_recovery__isnull=True)
        
        elif status == 'resolved':
            return queryset.filter(date_time_recovery__isnull=False)
        
        elif status == 'new':
            # Active incidents less than 1 hour old
            one_hour_ago = now - timedelta(hours=1)
            return queryset.filter(
                date_time_recovery__isnull=True,
                date_time_incident__gte=one_hour_ago
            )
        
        elif status == 'low':
            # Active incidents 1-2 hours old
            one_hour_ago = now - timedelta(hours=1)
            two_hours_ago = now - timedelta(hours=2)
            return queryset.filter(
                date_time_recovery__isnull=True,
                date_time_incident__lte=one_hour_ago,
                date_time_incident__gte=two_hours_ago
            )
        
        elif status == 'medium':
            # Active incidents 2-4 hours old
            two_hours_ago = now - timedelta(hours=2)
            four_hours_ago = now - timedelta(hours=4)
            return queryset.filter(
                date_time_recovery__isnull=True,
                date_time_incident__lte=two_hours_ago,
                date_time_incident__gte=four_hours_ago
            )
        
        elif status == 'critical':
            # Active incidents more than 4 hours old
            four_hours_ago = now - timedelta(hours=4)
            return queryset.filter(
                date_time_recovery__isnull=True,
                date_time_incident__lte=four_hours_ago
            )
        
        return queryset
    
    def _apply_network_specific_filters(self, queryset, search_form_data):
        """Apply network-specific filters based on model type - CORRECTED field names"""
        
        if self.model_class == TransportNetworkIncident:
            if search_form_data.get('region_loop'):
                queryset = queryset.filter(region_loop=search_form_data['region_loop'])
            
            if search_form_data.get('system_capacity'):
                queryset = queryset.filter(system_capacity=search_form_data['system_capacity'])
            
            if search_form_data.get('extremity_a'):
                queryset = queryset.filter(extremity_a__icontains=search_form_data['extremity_a'])
            
            if search_form_data.get('extremity_b'):
                queryset = queryset.filter(extremity_b__icontains=search_form_data['extremity_b'])
        
        elif self.model_class in [FileAccessNetworkIncident, RadioAccessNetworkIncident]:
            if search_form_data.get('do_wilaya'):  # CORRECTED: do_wilaya not wilaya
                queryset = queryset.filter(do_wilaya=search_form_data['do_wilaya'])
            
            if search_form_data.get('site'):
                queryset = queryset.filter(site__icontains=search_form_data['site'])
            
            if search_form_data.get('ip_address'):
                queryset = queryset.filter(ip_address__icontains=search_form_data['ip_address'])
            
            # File Access specific
            if (self.model_class == FileAccessNetworkIncident and 
                search_form_data.get('zone_metro')):
                queryset = queryset.filter(zone_metro__icontains=search_form_data['zone_metro'])
        
        elif self.model_class == CoreNetworkIncident:
            if search_form_data.get('platform'):
                queryset = queryset.filter(platform=search_form_data['platform'])
            
            if search_form_data.get('region_node'):
                queryset = queryset.filter(region_node=search_form_data['region_node'])
            
            if search_form_data.get('site'):
                queryset = queryset.filter(site__icontains=search_form_data['site'])
        
        elif self.model_class == BackboneInternetNetworkIncident:
            if search_form_data.get('interconnect_type'):
                queryset = queryset.filter(interconnect_type=search_form_data['interconnect_type'])
            
            if search_form_data.get('platform_igw'):
                queryset = queryset.filter(platform_igw=search_form_data['platform_igw'])
            
            if search_form_data.get('link_label'):
                queryset = queryset.filter(link_label__icontains=search_form_data['link_label'])
        
        return queryset
    
    def get_search_statistics(self, original_queryset, filtered_queryset):
        """Generate search statistics for display"""
        return {
            'total_incidents': original_queryset.count(),
            'filtered_incidents': filtered_queryset.count(),
            'active_incidents': filtered_queryset.filter(date_time_recovery__isnull=True).count(),
            'resolved_incidents': filtered_queryset.filter(date_time_recovery__isnull=False).count(),
        }
    
    def get_optimized_statistics(self, original_queryset, filtered_queryset):
        """Generate optimized search statistics for display"""
        # Use efficient count queries
        original_count = original_queryset.count()
        filtered_count = filtered_queryset.count()
    
        # Efficient active/resolved counts on filtered set
        active_count = filtered_queryset.filter(date_time_recovery__isnull=True).count()
        resolved_count = filtered_count - active_count
    
        return {
        'total_incidents': original_count,
        'filtered_incidents': filtered_count,
        'active_incidents': active_count,
        'resolved_incidents': resolved_count,
        }
    
    def get_bulk_incident_data(self, queryset, limit=None):
        """
        Optimized method for bulk incident data retrieval with minimal database hits
        """
        if limit:
            queryset = queryset[:limit]
        
        # Use values() to get only needed fields, reducing memory usage
        incident_data = queryset.values(
            'id', 'date_time_incident', 'date_time_recovery', 'duration_minutes',
            'cause', 'origin', 'impact_comment', 'is_resolved', 'is_archived',
            'created_by__username', 'updated_by__username'
        )
        
        return list(incident_data)

    def get_incident_summary_stats(self, queryset):
        """
        Get comprehensive statistics with a single database query
        """
        from django.db.models import Count, Q
        
        stats = queryset.aggregate(
            total_count=Count('id'),
            active_count=Count('id', filter=Q(date_time_recovery__isnull=True)),
            resolved_count=Count('id', filter=Q(date_time_recovery__isnull=False)),
            # Add severity-based counts
            new_count=Count('id', filter=Q(
                date_time_recovery__isnull=True,
                date_time_incident__gte=timezone.now() - timedelta(hours=1)
            )),
            critical_count=Count('id', filter=Q(
                date_time_recovery__isnull=True,
                date_time_incident__lte=timezone.now() - timedelta(hours=4)
            ))
        )
        
        return stats

# Factory function to get appropriate search service - CORRECTED network type mapping
def get_search_service(network_type):
    """Factory function to return appropriate search service"""
    
    # CORRECTED: Match your views.py NETWORKS dictionary keys
    model_mapping = {
        'transport': TransportNetworkIncident,
        'file_access': FileAccessNetworkIncident,  # CORRECTED: file_access not file-access
        'radio_access': RadioAccessNetworkIncident,  # CORRECTED: radio_access not radio-access
        'core': CoreNetworkIncident,
        'backbone_internet': BackboneInternetNetworkIncident,  # CORRECTED: backbone_internet not backbone-internet
    }
    
    model_class = model_mapping.get(network_type)
    if not model_class:
        raise ValueError(f"Unknown network type: {network_type}")
    
    return IncidentSearchService(model_class)

