from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

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
        
        # Prepare chart data
        trend_data_7d = get_chart_data_for_trends(network_models, days=7)
        trend_data_30d = get_chart_data_for_trends(network_models, days=30)
        network_comparison = get_network_comparison_data(network_stats)

        # Advanced analytics data
        hourly_distribution = get_hourly_distribution_data(network_models, days=7)
        network_trends = get_network_specific_trends(network_models, days=7)
        resolution_trends = get_resolution_time_trends(network_models, days=30)
        peak_analysis = get_peak_time_analysis(network_models, days=7)

        # Distribution analysis
        cause_distribution = get_cause_distribution(network_models, limit=10)
        origin_distribution = get_origin_distribution(network_models, limit=10)
        resolution_distribution = get_resolution_time_distribution(network_models)
        day_distribution = get_day_of_week_distribution(network_models, days=30)
        health_scores = get_network_health_score(network_stats)

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
            
            # Section A: Chart data (JSON-safe format for JavaScript)
            'chart_data': json.dumps({
                'trend_7d': trend_data_7d,
                'trend_30d': trend_data_30d,
                'network_comparison': network_comparison,
                'severity_distribution': overall_severity,

                # Section B advanced data
                'hourly_distribution': hourly_distribution,
                'network_trends': network_trends,
                'resolution_trends': resolution_trends,
                'peak_analysis': peak_analysis,

                # Section C distribution data
                'cause_distribution': cause_distribution,
                'origin_distribution': origin_distribution,
                'resolution_distribution': resolution_distribution,
                'day_distribution': day_distribution,
                'health_scores': health_scores,
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
    

def get_hourly_distribution_data(network_models, days=7):
    """Get hourly incident distribution for the last N days"""
    try:
        from collections import defaultdict
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Initialize 24-hour bins
        hourly_counts = defaultdict(int)
        
        for model in network_models.values():
            incidents = model.objects.filter(
                date_time_incident__gte=start_date,
                date_time_incident__lte=end_date
            )
            
            for incident in incidents:
                hour = incident.date_time_incident.hour
                hourly_counts[hour] += 1
        
        # Format for Chart.js
        hourly_data = []
        for hour in range(24):
            hourly_data.append({
                'hour': f"{hour:02d}:00",
                'count': hourly_counts.get(hour, 0)
            })
        
        return hourly_data
        
    except Exception as e:
        return [{'hour': f"{h:02d}:00", 'count': 0} for h in range(24)]


def get_network_specific_trends(network_models, days=7):
    """Get trend data for each network type separately"""
    try:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        # Create date range
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Network color scheme
        color_map = {
            'transport': '#0d6efd',
            'file_access': '#20c997',
            'radio_access': '#ffc107',
            'core': '#198754',
            'backbone_internet': '#6f42c1'
        }
        
        network_trends = {
            'labels': [date.strftime('%b %d') for date in date_range],
            'datasets': []
        }
        
        # Get data for each network
        for network_type, model in network_models.items():
            daily_counts = []
            
            for date in date_range:
                day_start = timezone.datetime.combine(date, timezone.datetime.min.time()).replace(tzinfo=timezone.get_current_timezone())
                day_end = day_start + timedelta(days=1)
                
                count = model.objects.filter(
                    date_time_incident__gte=day_start,
                    date_time_incident__lt=day_end
                ).count()
                
                daily_counts.append(count)
            
            network_trends['datasets'].append({
                'label': get_network_display_name(network_type),
                'data': daily_counts,
                'borderColor': color_map.get(network_type, '#6c757d'),
                'backgroundColor': color_map.get(network_type, '#6c757d') + '20',
                'borderWidth': 2,
                'tension': 0.4,
                'fill': False
            })
        
        return network_trends
        
    except Exception as e:
        return {'labels': [], 'datasets': []}


def get_resolution_time_trends(network_models, days=30):
    """Get average resolution time trends over time"""
    try:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        resolution_data = []
        
        # Group by weeks for 30-day view
        current_date = start_date
        while current_date <= end_date:
            week_end = current_date + timedelta(days=7)
            if week_end > end_date:
                week_end = end_date
            
            week_start_dt = timezone.datetime.combine(current_date, timezone.datetime.min.time()).replace(tzinfo=timezone.get_current_timezone())
            week_end_dt = timezone.datetime.combine(week_end, timezone.datetime.max.time()).replace(tzinfo=timezone.get_current_timezone())
            
            total_resolution_minutes = 0
            resolved_count = 0
            
            for model in network_models.values():
                incidents = model.objects.filter(
                    date_time_recovery__isnull=False,
                    date_time_recovery__gte=week_start_dt,
                    date_time_recovery__lte=week_end_dt
                )
                
                for incident in incidents:
                    if incident.duration_minutes:
                        total_resolution_minutes += incident.duration_minutes
                        resolved_count += 1
            
            avg_hours = (total_resolution_minutes / resolved_count / 60) if resolved_count > 0 else 0
            
            resolution_data.append({
                'week': f"{current_date.strftime('%b %d')}-{week_end.strftime('%d')}",
                'avg_hours': round(avg_hours, 1),
                'count': resolved_count
            })
            
            current_date = week_end + timedelta(days=1)
        
        return resolution_data
        
    except Exception as e:
        return []


def get_peak_time_analysis(network_models, days=7):
    """Identify peak incident times and provide summary"""
    try:
        from collections import defaultdict
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        hourly_counts = defaultdict(int)
        daily_counts = defaultdict(int)
        
        for model in network_models.values():
            incidents = model.objects.filter(
                date_time_incident__gte=start_date,
                date_time_incident__lte=end_date
            )
            
            for incident in incidents:
                hour = incident.date_time_incident.hour
                day = incident.date_time_incident.strftime('%A')
                hourly_counts[hour] += 1
                daily_counts[day] += 1
        
        # Find peaks
        peak_hour = max(hourly_counts.items(), key=lambda x: x[1]) if hourly_counts else (0, 0)
        peak_day = max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else ('N/A', 0)
        
        return {
            'peak_hour': f"{peak_hour[0]:02d}:00",
            'peak_hour_count': peak_hour[1],
            'peak_day': peak_day[0],
            'peak_day_count': peak_day[1],
            'hourly_data': dict(hourly_counts),
            'daily_data': dict(daily_counts)
        }
        
    except Exception as e:
        return {
            'peak_hour': 'N/A',
            'peak_hour_count': 0,
            'peak_day': 'N/A',
            'peak_day_count': 0,
            'hourly_data': {},
            'daily_data': {}
        }
    
def get_cause_distribution(network_models, limit=10):
    """Get top causes of incidents with counts"""
    try:
        from collections import Counter
        
        causes = []
        for model in network_models.values():
            incidents = model.objects.filter(
                cause__isnull=False
            ).exclude(cause='')
            
            for incident in incidents:
                cause = incident.get_cause_display()
                causes.append(cause)
        
        # Count occurrences
        cause_counts = Counter(causes)
        top_causes = cause_counts.most_common(limit)
        
        return {
            'labels': [cause for cause, count in top_causes],
            'data': [count for cause, count in top_causes],
            'total': len(causes)
        }
        
    except Exception as e:
        return {'labels': [], 'data': [], 'total': 0}


def get_origin_distribution(network_models, limit=10):
    """Get top origins of incidents with counts"""
    try:
        from collections import Counter
        
        origins = []
        for model in network_models.values():
            incidents = model.objects.filter(
                origin__isnull=False
            ).exclude(origin='')
            
            for incident in incidents:
                origin = incident.get_origin_display()
                origins.append(origin)
        
        # Count occurrences
        origin_counts = Counter(origins)
        top_origins = origin_counts.most_common(limit)
        
        return {
            'labels': [origin for origin, count in top_origins],
            'data': [count for origin, count in top_origins],
            'total': len(origins)
        }
        
    except Exception as e:
        return {'labels': [], 'data': [], 'total': 0}


def get_resolution_time_distribution(network_models):
    """Get distribution of resolution times in buckets"""
    try:
        from collections import defaultdict
        
        # Define time buckets (in minutes)
        buckets = {
            '0-30 min': (0, 30),
            '30-60 min': (30, 60),
            '1-2 hours': (60, 120),
            '2-4 hours': (120, 240),
            '4-8 hours': (240, 480),
            '8-24 hours': (480, 1440),
            '1-3 days': (1440, 4320),
            '3+ days': (4320, float('inf'))
        }
        
        bucket_counts = defaultdict(int)
        
        for model in network_models.values():
            incidents = model.objects.filter(
                date_time_recovery__isnull=False,
                duration_minutes__isnull=False
            )
            
            for incident in incidents:
                duration = incident.duration_minutes
                for bucket_name, (min_val, max_val) in buckets.items():
                    if min_val <= duration < max_val:
                        bucket_counts[bucket_name] += 1
                        break
        
        # Prepare data in order
        ordered_labels = [
            '0-30 min', '30-60 min', '1-2 hours', '2-4 hours',
            '4-8 hours', '8-24 hours', '1-3 days', '3+ days'
        ]
        
        return {
            'labels': ordered_labels,
            'data': [bucket_counts.get(label, 0) for label in ordered_labels]
        }
        
    except Exception as e:
        return {'labels': [], 'data': []}


def get_day_of_week_distribution(network_models, days=30):
    """Get incident distribution by day of week"""
    try:
        from collections import defaultdict
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        day_counts = defaultdict(int)
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for model in network_models.values():
            incidents = model.objects.filter(
                date_time_incident__gte=start_date,
                date_time_incident__lte=end_date
            )
            
            for incident in incidents:
                day_name = incident.date_time_incident.strftime('%A')
                day_counts[day_name] += 1
        
        return {
            'labels': day_order,
            'data': [day_counts.get(day, 0) for day in day_order],
            'peak_day': max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else 'N/A'
        }
        
    except Exception as e:
        return {'labels': [], 'data': [], 'peak_day': 'N/A'}


def get_network_health_score(network_stats):
    """Calculate health score for each network (0-100)"""
    try:
        health_scores = {}
        
        for network_type, stats in network_stats.items():
            total = stats['total']
            active = stats['active']
            
            if total == 0:
                health_score = 100
            else:
                # Calculate based on active incidents ratio and severity
                active_ratio = active / total
                severity_counts = stats['severity_counts']
                
                # Weight by severity
                severity_score = (
                    severity_counts['new'] * 0.9 +
                    severity_counts['low'] * 0.7 +
                    severity_counts['medium'] * 0.4 +
                    severity_counts['critical'] * 0.1
                ) / max(active, 1)
                
                # Combine factors
                health_score = int((1 - active_ratio * 0.5) * severity_score * 100)
                health_score = max(0, min(100, health_score))
            
            health_scores[network_type] = {
                'name': stats['name'],
                'score': health_score,
                'status': get_health_status(health_score)
            }
        
        return health_scores
        
    except Exception as e:
        return {}


def get_health_status(score):
    """Convert health score to status label"""
    if score >= 90:
        return 'Excellent'
    elif score >= 75:
        return 'Good'
    elif score >= 60:
        return 'Fair'
    elif score >= 40:
        return 'Poor'
    else:
        return 'Critical'
    
@login_required
@require_http_methods(["GET"])
def refresh_chart_data(request):
    """AJAX endpoint to refresh chart data without page reload"""
    try:
        # Define network models
        network_models = {
            'transport': TransportNetworkIncident,
            'file_access': FileAccessNetworkIncident,
            'radio_access': RadioAccessNetworkIncident,
            'core': CoreNetworkIncident,
            'backbone_internet': BackboneInternetNetworkIncident,
        }
        
        # Get refresh parameters from request
        period = request.GET.get('period', '7')  # 7 or 30 days
        days = int(period)
        
        # Calculate statistics
        total_incidents = sum(model.objects.count() for model in network_models.values())
        active_incidents = sum(
            model.objects.filter(date_time_recovery__isnull=True).count() 
            for model in network_models.values()
        )
        
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        resolved_today = sum(
            model.objects.filter(
                date_time_recovery__isnull=False,
                date_time_recovery__gte=today_start
            ).count()
            for model in network_models.values()
        )
        
        # Get network stats for severity
        network_stats = {}
        for network_type, model in network_models.items():
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
            
            network_stats[network_type] = {
                'name': get_network_display_name(network_type),
                'total': model.objects.count(),
                'active': active_incidents_qs.count(),
                'severity_counts': severity_counts,
            }
        
        # Calculate overall severity
        overall_severity = {
            'new': sum(stats['severity_counts']['new'] for stats in network_stats.values()),
            'low': sum(stats['severity_counts']['low'] for stats in network_stats.values()),
            'medium': sum(stats['severity_counts']['medium'] for stats in network_stats.values()),
            'critical': sum(stats['severity_counts']['critical'] for stats in network_stats.values()),
        }
        
        # Prepare chart data based on requested period
        trend_data = get_chart_data_for_trends(network_models, days=days)
        hourly_distribution = get_hourly_distribution_data(network_models, days=days)
        network_trends = get_network_specific_trends(network_models, days=days)
        peak_analysis = get_peak_time_analysis(network_models, days=days)
        network_comparison = get_network_comparison_data(network_stats)
        
        # Return JSON response
        return JsonResponse({
            'success': True,
            'timestamp': now.isoformat(),
            'stats': {
                'total_incidents': total_incidents,
                'active_incidents': active_incidents,
                'resolved_today': resolved_today,
            },
            'charts': {
                'trend': trend_data,
                'severity': overall_severity,
                'hourly': hourly_distribution,
                'network_trends': network_trends,
                'network_comparison': network_comparison,
                'peak_analysis': peak_analysis,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)