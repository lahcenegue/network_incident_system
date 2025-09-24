from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models
import ipaddress
import re
from datetime import timedelta

class IncidentValidators:
    """Custom validators for incident forms"""
    
    @staticmethod
    def validate_ip_address(ip_string):
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip_string)
            return True
        except ValueError:
            raise ValidationError(f"'{ip_string}' is not a valid IP address format")
    
    @staticmethod
    def validate_recovery_time(incident_time, recovery_time):
        """Ensure recovery time is after incident time"""
        if recovery_time and incident_time:
            if recovery_time <= incident_time:
                raise ValidationError(
                    "Recovery time must be after the incident time"
                )
            
            # Check if recovery time is not too far in the future (max 30 days)
            max_recovery = incident_time + timedelta(days=30)
            if recovery_time > max_recovery:
                raise ValidationError(
                    "Recovery time cannot be more than 30 days after incident time"
                )
    
    @staticmethod
    def validate_incident_time(incident_time):
        """Validate incident time is reasonable"""
        if incident_time:
            now = timezone.now()
            
            # Cannot be more than 1 year in the past
            min_time = now - timedelta(days=365)
            if incident_time < min_time:
                raise ValidationError(
                    "Incident time cannot be more than 1 year in the past"
                )
            
            # Cannot be more than 24 hours in the future
            max_time = now + timedelta(hours=24)
            if incident_time > max_time:
                raise ValidationError(
                    "Incident time cannot be more than 24 hours in the future"
                )
    
    @staticmethod
    def validate_extremity_consistency(extremity_a, dot_extremity_a, extremity_b, dot_extremity_b):
        """Validate extremity fields are consistent"""
        if extremity_a and not dot_extremity_a:
            raise ValidationError(
                "DOT Extremity A is required when Extremity A is provided"
            )
        
        if extremity_b and not dot_extremity_b:
            raise ValidationError(
                "DOT Extremity B is required when Extremity B is provided"
            )
        
        if extremity_a and extremity_b and extremity_a.strip().lower() == extremity_b.strip().lower():
            raise ValidationError(
                "Extremity A and Extremity B cannot be the same location"
            )
    
    @staticmethod
    def validate_site_name(site_name, network_type):
        """Validate site name format based on network type"""
        if not site_name:
            return
        
        # Remove extra whitespace
        site_name = site_name.strip()
        
        if len(site_name) < 2:
            raise ValidationError(
                "Site name must be at least 2 characters long"
            )
        
        if len(site_name) > 50:
            raise ValidationError(
                "Site name cannot exceed 50 characters"
            )
        
        # Check for valid characters (alphanumeric, spaces, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', site_name):
            raise ValidationError(
                "Site name can only contain letters, numbers, spaces, hyphens, and underscores"
            )

class DuplicateIncidentChecker:
    """Check for potential duplicate incidents"""
    
    @staticmethod
    def check_transport_duplicate(network_type, extremity_a, extremity_b, incident_time, exclude_id=None):
        """Check for duplicate transport network incidents"""
        from .models import TransportNetworkIncident
        
        # Look for incidents with same extremities within 1 hour
        time_window_start = incident_time - timedelta(hours=1)
        time_window_end = incident_time + timedelta(hours=1)
        
        query = TransportNetworkIncident.objects.filter(
            extremity_a__iexact=extremity_a,
            extremity_b__iexact=extremity_b,
            date_time_incident__gte=time_window_start,
            date_time_incident__lte=time_window_end,
            date_time_recovery__isnull=True  # Only check active incidents
        )
        
        if exclude_id:
            query = query.exclude(id=exclude_id)
        
        if query.exists():
            raise ValidationError(
                f"A similar incident for {extremity_a} to {extremity_b} already exists within the last hour"
            )
    
    @staticmethod
    def check_ip_based_duplicate(model_class, ip_address, incident_time, exclude_id=None):
        """Check for duplicate incidents based on IP address"""
        time_window_start = incident_time - timedelta(hours=2)
        time_window_end = incident_time + timedelta(hours=2)
        
        query = model_class.objects.filter(
            ip_address=ip_address,
            date_time_incident__gte=time_window_start,
            date_time_incident__lte=time_window_end,
            date_time_recovery__isnull=True
        )
        
        if exclude_id:
            query = query.exclude(id=exclude_id)
        
        if query.exists():
            raise ValidationError(
                f"A similar incident for IP {ip_address} already exists within the last 2 hours"
            )
    
    @staticmethod
    def check_site_duplicate(model_class, site, incident_time, exclude_id=None):
        """Check for duplicate incidents based on site"""
        time_window_start = incident_time - timedelta(hours=1)
        time_window_end = incident_time + timedelta(hours=1)
        
        query = model_class.objects.filter(
            site__iexact=site,
            date_time_incident__gte=time_window_start,
            date_time_incident__lte=time_window_end,
            date_time_recovery__isnull=True
        )
        
        if exclude_id:
            query = query.exclude(id=exclude_id)
        
        if query.exists():
            raise ValidationError(
                f"A similar incident for site '{site}' already exists within the last hour"
            )