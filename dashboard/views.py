from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
import json
from incidents.models import (
    TransportNetworkIncident, FileAccessNetworkIncident, 
    RadioAccessNetworkIncident, CoreNetworkIncident, 
    BackboneInternetNetworkIncident
)

@login_required
def dashboard_view(request):
    """Enhanced dashboard with real-time analytics and chart data"""
    try:
        # Define all network models for comprehensive statistics
        network_models = {
            'transport': TransportNetworkIncident,
            'file_access': FileAccessNetworkIncident,
            'radio_access': RadioAccessNetworkIncident,
            'core': CoreNetworkIncident,
            'backbone_internet': BackboneInternetNetworkIncident,
        }
        
        # Calculate overall statistics
        total_incidents = 0
        active_incidents = 0
        resolved_today = 0
        
        # Network-specific statistics
        network_stats = {}
        
        # Time references for calculations
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for network_type, model in network_models.items():
            # Get total incidents for this network
            total_count = model.objects.count()
            total_incidents += total_count
            
            # Get active incidents (no recovery time)
            active_count = model.objects.filter(date_time_recovery__isnull=True).count()
            active_incidents += active_count
            
            # Get incidents resolved today
            resolved_today_count = model.objects.filter(
                date_time_recovery__isnull=False,
                date_time_recovery__gte=today_start
            ).count()
            resolved_today += resolved_today_count
            
            # Calculate severity distribution for active incidents
            active_incidents_qs = model.objects.filter(date_time_recovery__isnull=True)
            severity_counts = {'new': 0, 'low': 0, 'medium': 0, 'critical': 0}
            
            for incident in active_incidents_qs:
                severity = incident.get_severity_class()
                if severity == 'incident-new':
                    severity_counts['new'] += 1
                elif severity == 'incident-low':
                    severity_counts['low'] += 1
                elif severity == 'incident-medium':
                    severity_counts['medium'] += 1
                elif severity == 'incident-critical':
                    severity_counts['critical'] += 1
            
            # Store network-specific stats
            network_stats[network_type] = {
                'name': get_network_display_name(network_type),
                'total': total_count,
                'active': active_count,
                'resolved_today': resolved_today_count,
                'severity_counts': severity_counts,
                'icon': get_network_icon(network_type)
            }
        
        # Calculate average resolution time (MTTR) for last 30 days
        thirty_days_ago = now - timedelta(days=30)
        avg_resolution_time = calculate_average_resolution_time(network_models, thirty_days_ago)
        
        # Get recent incidents across all networks (last 10)
        recent_incidents = get_recent_incidents(network_models, limit=10)
        
        # Calculate overall severity distribution
        overall_severity = {
            'new': sum(stats['severity_counts']['new'] for stats in network_stats.values()),
            'low': sum(stats['severity_counts']['low'] for stats in network_stats.values()),
            'medium': sum(stats['severity_counts']['medium'] for stats in network_stats.values()),
            'critical': sum(stats['severity_counts']['critical'] for stats in network_stats.values()),
        }
        
        # NEW: Prepare chart data
        trend_data_7d = get_chart_data_for_trends(network_models, days=7)
        trend_data_30d = get_chart_data_for_trends(network_models, days=30)
        network_comparison = get_network_comparison_data(network_stats)
        
        context = {
            'user': request.user,
            
            # Main statistics cards
            'total_incidents': total_incidents,
            'active_incidents': active_incidents,
            'resolved_incidents': resolved_today,
            'avg_resolution_time': avg_resolution_time,
            
            # Network-specific data for overview section
            'network_stats': network_stats,
            
            # Recent incidents
            'recent_incidents': recent_incidents,
            
            # Severity distribution for charts
            'overall_severity': overall_severity,
            
            # Individual network breakdowns (for existing template variables)
            'transport_active': network_stats.get('transport', {}).get('active', 0),
            'transport_total': network_stats.get('transport', {}).get('total', 0),
            'file_access_active': network_stats.get('file_access', {}).get('active', 0),
            'file_access_total': network_stats.get('file_access', {}).get('total', 0),
            'radio_access_active': network_stats.get('radio_access', {}).get('active', 0),
            'radio_access_total': network_stats.get('radio_access', {}).get('total', 0),
            'core_active': network_stats.get('core', {}).get('active', 0),
            'core_total': network_stats.get('core', {}).get('total', 0),
            'backbone_active': network_stats.get('backbone_internet', {}).get('active', 0),
            'backbone_total': network_stats.get('backbone_internet', {}).get('total', 0),
            
            # NEW: Chart data (JSON-safe format for JavaScript)
            'chart_data': json.dumps({
                'trend_7d': trend_data_7d,
                'trend_30d': trend_data_30d,
                'network_comparison': network_comparison,
                'severity_distribution': overall_severity,
            }),
        }
        
        return render(request, 'dashboard/dashboard.html', context)
        
    except Exception as e:
        # Fallback context in case of errors
        context = {
            'user': request.user,
            'total_incidents': 0,
            'active_incidents': 0,
            'resolved_incidents': 0,
            'avg_resolution_time': 'N/A',
            'network_stats': {},
            'recent_incidents': [],
            'overall_severity': {'new': 0, 'low': 0, 'medium': 0, 'critical': 0},
            'chart_data': json.dumps({}),
            'error': str(e)
        }
        return render(request, 'dashboard/dashboard.html', context)


def get_network_display_name(network_type):
    """Return display name for network type"""
    names = {
        'transport': 'Transport Networks',
        'file_access': 'File Access Networks',
        'radio_access': 'Radio Access Networks',
        'core': 'Core Networks',
        'backbone_internet': 'Backbone Internet Networks',
    }
    return names.get(network_type, network_type.replace('_', ' ').title())


def get_network_icon(network_type):
    """Return Bootstrap icon class for network type"""
    icons = {
        'transport': 'bi-diagram-3',
        'file_access': 'bi-hdd-network',
        'radio_access': 'bi-broadcast-pin',
        'core': 'bi-cpu',
        'backbone_internet': 'bi-globe',
    }
    return icons.get(network_type, 'bi-network')


def calculate_average_resolution_time(network_models, since_date):
    """Calculate average resolution time across all networks"""
    try:
        total_resolved_incidents = 0
        total_resolution_minutes = 0
        
        for model in network_models.values():
            resolved_incidents = model.objects.filter(
                date_time_recovery__isnull=False,
                date_time_recovery__gte=since_date
            )
            
            for incident in resolved_incidents:
                if incident.duration_minutes:
                    total_resolved_incidents += 1
                    total_resolution_minutes += incident.duration_minutes
        
        if total_resolved_incidents > 0:
            avg_minutes = total_resolution_minutes / total_resolved_incidents
            
            # Convert to human-readable format
            if avg_minutes < 60:
                return f"{int(avg_minutes)}m"
            elif avg_minutes < 1440:  # Less than 24 hours
                hours = int(avg_minutes / 60)
                minutes = int(avg_minutes % 60)
                return f"{hours}h {minutes}m"
            else:  # Days
                days = int(avg_minutes / 1440)
                hours = int((avg_minutes % 1440) / 60)
                return f"{days}d {hours}h"
        
        return "N/A"
        
    except Exception as e:
        return "N/A"


def get_recent_incidents(network_models, limit=10):
    """Get recent incidents across all networks"""
    try:
        all_incidents = []
        
        for network_type, model in network_models.items():
            incidents = model.objects.select_related('created_by').order_by('-created_at')[:limit]
            
            for incident in incidents:
                # Add network type and location info to each incident
                incident.network_type = get_network_display_name(network_type)
                incident.location = getattr(incident, 'get_location_display', lambda: 'N/A')()
                incident.duration = incident.get_duration_display()
                all_incidents.append(incident)
        
        # Sort all incidents by creation date and limit to specified number
        all_incidents.sort(key=lambda x: x.created_at, reverse=True)
        return all_incidents[:limit]
        
    except Exception as e:
        return []


def get_chart_data_for_trends(network_models, days=7):
    """Get trend data for the last N days"""
    try:
        from django.db.models import Count
        from datetime import datetime, timedelta
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # Create date range
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Get incident counts per day
        trend_data = []
        for date in date_range:
            day_start = timezone.datetime.combine(date, timezone.datetime.min.time()).replace(tzinfo=timezone.get_current_timezone())
            day_end = day_start + timedelta(days=1)
            
            day_count = 0
            for model in network_models.values():
                day_count += model.objects.filter(
                    date_time_incident__gte=day_start,
                    date_time_incident__lt=day_end
                ).count()
            
            trend_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': day_count,
                'display_date': date.strftime('%b %d')
            })
        
        return trend_data
        
    except Exception as e:
        # Return empty data structure
        return []


def get_network_comparison_data(network_stats):
    """Format network data for comparison charts"""
    try:
        chart_data = {
            'labels': [],
            'active_data': [],
            'total_data': [],
            'colors': []
        }
        
        # Network color scheme matching your CSS
        color_map = {
            'transport': '#0d6efd',
            'file_access': '#20c997', 
            'radio_access': '#ffc107',
            'core': '#198754',
            'backbone_internet': '#6f42c1'
        }
        
        for network_type, stats in network_stats.items():
            chart_data['labels'].append(stats['name'])
            chart_data['active_data'].append(stats['active'])
            chart_data['total_data'].append(stats['total'])
            chart_data['colors'].append(color_map.get(network_type, '#6c757d'))
        
        return chart_data
        
    except Exception as e:
        return {'labels': [], 'active_data': [], 'total_data': [], 'colors': []}