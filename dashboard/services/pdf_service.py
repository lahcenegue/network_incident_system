"""
PDF Report Generation Service
Handles filtering, statistics calculation, and PDF generation for incident reports
"""

import os
from datetime import datetime, timedelta
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models import Count, Avg, Q, F
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

from incidents.models import (
    TransportNetworkIncident,
    FileAccessNetworkIncident, 
    RadioAccessNetworkIncident,
    CoreNetworkIncident,
    BackboneInternetNetworkIncident
)


class PDFReportGenerator:
    """
    Main PDF Report Generator Class
    Handles data filtering, statistics calculation, and PDF generation
    """
    
    def __init__(self, start_date, end_date, user):
        """
        Initialize PDF generator with date range and user
        
        Args:
            start_date: datetime object - start of report period
            end_date: datetime object - end of report period
            user: User object - user generating the report
        """
        self.start_date = start_date
        self.end_date = end_date
        self.user = user
        self.incidents_data = {}
        self.statistics = {}
        self.network_models = {
            'transport': TransportNetworkIncident,
            'file_access': FileAccessNetworkIncident,
            'radio_access': RadioAccessNetworkIncident,
            'core': CoreNetworkIncident,
            'backbone_internet': BackboneInternetNetworkIncident,
        }
        
    def filter_incidents_by_date(self):
        """
        Filter incidents for all network types within date range
        Returns dict with network_type as key and queryset as value
        """
        filtered_data = {}
        
        for network_type, model in self.network_models.items():
            # Filter incidents within date range
            incidents = model.objects.filter(
                date_time_incident__gte=self.start_date,
                date_time_incident__lte=self.end_date
            ).select_related('created_by').order_by('-date_time_incident')
            
            filtered_data[network_type] = {
                'incidents': incidents,
                'count': incidents.count(),
                'active': incidents.filter(date_time_recovery__isnull=True).count(),
                'resolved': incidents.filter(date_time_recovery__isnull=False).count(),
            }
        
        self.incidents_data = filtered_data
        return filtered_data
    
    def calculate_statistics(self):
        """
        Calculate comprehensive statistics for the report period
        """
        stats = {
            'total_incidents': 0,
            'total_active': 0,
            'total_resolved': 0,
            'networks': {},
            'severity_breakdown': {
                'new': 0,
                'low': 0, 
                'medium': 0,
                'critical': 0,
                'resolved': 0
            },
            'top_causes': {},
            'top_origins': {},
            'avg_resolution_time': None,
        }
        
        # Calculate totals across all networks
        for network_type, data in self.incidents_data.items():
            stats['total_incidents'] += data['count']
            stats['total_active'] += data['active']
            stats['total_resolved'] += data['resolved']
            
            # Network-specific stats
            stats['networks'][network_type] = {
                'total': data['count'],
                'active': data['active'],
                'resolved': data['resolved'],
                'name': self._get_network_display_name(network_type)
            }
            
            # Severity breakdown
            for incident in data['incidents']:
                severity = incident.get_severity_display().lower()
                if severity in stats['severity_breakdown']:
                    stats['severity_breakdown'][severity] += 1
            
            # Causes and origins
            for incident in data['incidents']:
                if incident.cause:
                    stats['top_causes'][incident.cause] = stats['top_causes'].get(incident.cause, 0) + 1
                if incident.origin:
                    stats['top_origins'][incident.origin] = stats['top_origins'].get(incident.origin, 0) + 1
        
        # Sort top causes and origins (get top 10)
        stats['top_causes'] = dict(sorted(stats['top_causes'].items(), key=lambda x: x[1], reverse=True)[:10])
        stats['top_origins'] = dict(sorted(stats['top_origins'].items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Calculate average resolution time
        stats['avg_resolution_time'] = self._calculate_avg_resolution_time()
        
        self.statistics = stats
        return stats
    
    def _calculate_avg_resolution_time(self):
        """Calculate average resolution time for resolved incidents in hours"""
        total_duration = timedelta()
        resolved_count = 0
        
        for network_type, data in self.incidents_data.items():
            resolved_incidents = data['incidents'].filter(date_time_recovery__isnull=False)
            for incident in resolved_incidents:
                if incident.date_time_recovery and incident.date_time_incident:
                    duration = incident.date_time_recovery - incident.date_time_incident
                    total_duration += duration
                    resolved_count += 1
        
        if resolved_count > 0:
            avg_seconds = total_duration.total_seconds() / resolved_count
            avg_hours = avg_seconds / 3600
            return round(avg_hours, 2)
        return None
    
    def _get_network_display_name(self, network_type):
        """Get display name for network type"""
        names = {
            'transport': 'Transport Networks',
            'file_access': 'File Access Networks',
            'radio_access': 'Radio Access Networks',
            'core': 'Core Networks',
            'backbone_internet': 'Backbone Internet Networks',
        }
        return names.get(network_type, network_type.title())
    
    def prepare_chart_data(self):
        """
        Prepare data for charts (will be rendered as tables in PDF)
        Returns dict with chart data ready for template rendering
        """
        chart_data = {}
        
        # 1. Network comparison data
        chart_data['network_comparison'] = []
        for network_type, stats in self.statistics['networks'].items():
            chart_data['network_comparison'].append({
                'network': stats['name'],
                'total': stats['total'],
                'active': stats['active'],
                'resolved': stats['resolved'],
                'percentage': round((stats['total'] / self.statistics['total_incidents'] * 100) if self.statistics['total_incidents'] > 0 else 0, 1)
            })
        
        # 2. Severity distribution
        chart_data['severity_distribution'] = [
            {'label': 'New (<1hr)', 'value': self.statistics['severity_breakdown']['new'], 'color': '#f8f9fa'},
            {'label': 'Low (1-2hr)', 'value': self.statistics['severity_breakdown']['low'], 'color': '#ffc107'},
            {'label': 'Medium (2-4hr)', 'value': self.statistics['severity_breakdown']['medium'], 'color': '#fd7e14'},
            {'label': 'Critical (>4hr)', 'value': self.statistics['severity_breakdown']['critical'], 'color': '#dc3545'},
            {'label': 'Resolved', 'value': self.statistics['severity_breakdown']['resolved'], 'color': '#198754'},
        ]
        
        # 3. Top causes
        chart_data['top_causes'] = [
            {'cause': k, 'count': v} 
            for k, v in list(self.statistics['top_causes'].items())[:5]
        ]
        
        # 4. Top origins  
        chart_data['top_origins'] = [
            {'origin': k, 'count': v}
            for k, v in list(self.statistics['top_origins'].items())[:5]
        ]
        
        return chart_data
    
    def generate_pdf(self):
        """
        Main PDF generation method
        Returns PDF content as bytes
        """
        # Step 1: Filter incidents
        self.filter_incidents_by_date()
        
        # Step 2: Calculate statistics
        self.calculate_statistics()
        
        # Step 3: Prepare chart data
        chart_data = self.prepare_chart_data()
        
        # Step 4: Get recent incidents (max 50 for PDF)
        recent_incidents = self._get_recent_incidents_for_pdf(limit=50)
        
        # Step 5: Prepare context for template
        context = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'generated_date': datetime.now(),
            'generated_by': self.user.get_full_name() or self.user.username,
            'statistics': self.statistics,
            'chart_data': chart_data,
            'recent_incidents': recent_incidents,
            'logo_path': self._get_logo_path(),
        }
        
        # Step 6: Render HTML template
        html_string = render_to_string('reports/pdf_report.html', context)
        
        # Step 7: Generate PDF with WeasyPrint
        # Convert BASE_DIR to string for WeasyPrint compatibility
        base_url = str(settings.BASE_DIR)
        
        font_config = FontConfiguration()
        html = HTML(string=html_string, base_url=base_url)  # Use string, not WindowsPath
        pdf_content = html.write_pdf(font_config=font_config)
        
        return pdf_content
    
    def _get_recent_incidents_for_pdf(self, limit=50):
        """Get recent incidents from all networks for PDF table"""
        all_incidents = []
        
        for network_type, data in self.incidents_data.items():
            for incident in data['incidents'][:limit]:
                all_incidents.append({
                    'id': str(incident.id)[:8],  # Short ID
                    'network': self._get_network_display_name(network_type),
                    'date_time': incident.date_time_incident,
                    'duration': incident.get_duration_display(),
                    'severity': incident.get_severity_display(),
                    'status': 'Resolved' if incident.date_time_recovery else 'Active',
                    'cause': incident.cause or 'Not specified',
                })
        
        # Sort by date descending and limit
        all_incidents.sort(key=lambda x: x['date_time'], reverse=True)
        return all_incidents[:limit]
    
    
    def _get_logo_path(self):
        """Get absolute file path for logo"""
        # Convert BASE_DIR to string for Windows compatibility
        base_dir_str = str(settings.BASE_DIR)
        
        logo_path = os.path.join(
            base_dir_str,
            'incident_management',
            'static',
            'images',
            'reports',
            'company_logo.svg'
        )
        
        # Convert Windows backslashes to forward slashes for WeasyPrint
        logo_path = logo_path.replace('\\', '/')
        
        # WeasyPrint needs file:/// URI
        return f"file:///{logo_path}"
    
    def save_to_server(self, pdf_content):
        """
        Save PDF to server storage
        Returns file path
        """
        # Ensure reports directory exists
        reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_str = self.start_date.strftime('%Y-%m-%d')
        end_str = self.end_date.strftime('%Y-%m-%d')
        filename = f'incident_report_{start_str}_to_{end_str}_{timestamp}.pdf'
        filepath = os.path.join(reports_dir, filename)
        
        # Save PDF
        with open(filepath, 'wb') as f:
            f.write(pdf_content)
        
        return filepath