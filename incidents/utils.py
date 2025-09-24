from django.utils import timezone
from datetime import timedelta

def get_incident_color_class(incident):
    """
    Determine the CSS color class based on incident status and duration
    
    Returns:
    - 'incident-resolved' (green) for resolved incidents
    - 'incident-critical' (red) for active incidents > 4 hours
    - 'incident-major' (orange) for active incidents 2-4 hours
    - 'incident-minor' (yellow) for active incidents 1-2 hours
    - 'incident-new' (white) for active incidents < 1 hour
    """
    
    # If incident is resolved (has recovery time), it's green
    if incident.date_time_recovery:
        return 'incident-resolved'
    
    # For active incidents, calculate duration
    if incident.date_time_incident:
        now = timezone.now()
        duration = now - incident.date_time_incident
        
        # Convert to hours for comparison
        hours = duration.total_seconds() / 3600
        
        if hours > 4:
            return 'incident-critical'  # Red background
        elif hours > 2:
            return 'incident-major'     # Orange background
        elif hours > 1:
            return 'incident-minor'     # Yellow background
        else:
            return 'incident-new'       # White background
    
    # Default fallback
    return 'incident-new'

def format_incident_duration(incident):
    """
    Format the incident duration in a human-readable format
    Returns: "Xd Yh Zm" format
    """
    if not incident.date_time_incident:
        return "Unknown"
    
    # Determine end time (recovery time or current time for active incidents)
    end_time = incident.date_time_recovery or timezone.now()
    duration = end_time - incident.date_time_incident
    
    # Calculate days, hours, and minutes
    total_seconds = int(duration.total_seconds())
    days = total_seconds // (24 * 3600)
    hours = (total_seconds % (24 * 3600)) // 3600
    minutes = (total_seconds % 3600) // 60
    
    # Format the string
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or len(parts) == 0:  # Always show minutes if nothing else
        parts.append(f"{minutes}m")
    
    return " ".join(parts)

def validate_incident_data(incident_data, network_type):
    """
    Perform additional validation on incident data
    Returns: (is_valid, error_messages)
    """
    errors = []
    
    # Check required fields based on network type
    required_fields = get_required_fields_by_network(network_type)
    
    for field in required_fields:
        if field not in incident_data or not incident_data[field]:
            field_name = field.replace('_', ' ').title()
            errors.append(f"{field_name} is required")
    
    # Validate date consistency
    incident_time = incident_data.get('date_time_incident')
    recovery_time = incident_data.get('date_time_recovery')
    
    if incident_time and recovery_time:
        if recovery_time <= incident_time:
            errors.append("Recovery time must be after incident time")
    
    return len(errors) == 0, errors

def get_required_fields_by_network(network_type):
    """
    Return list of required fields for each network type
    """
    field_map = {
        'transport': [
            'date_time_incident', 'region_loop', 'system_capacity', 
            'extremity_a', 'extremity_b', 'dot_extremity_b'
        ],
        'file_access': [
            'date_time_incident', 'do_wilaya', 'zone_metro', 'site', 'ip_address'
        ],
        'radio_access': [
            'date_time_incident', 'do_wilaya', 'site', 'ip_address'
        ],
        'core': [
            'date_time_incident', 'platform', 'region_node', 'extremity_a', 'extremity_b', 'dot_extremity_b'
        ],
        'backbone_internet': [
            'date_time_incident', 'interconnect_type', 'platform_igw', 'link_label'
        ]
    }
    return field_map.get(network_type, [])

def get_network_statistics(network_type, model_class):
    """
    Get statistics for a specific network type
    Returns: dict with counts and percentages
    """
    try:
        total = model_class.objects.count()
        active = model_class.objects.filter(date_time_recovery__isnull=True).count()
        resolved = model_class.objects.filter(date_time_recovery__isnull=False).count()
        
        # Get incidents by severity (for active incidents only)
        active_incidents = model_class.objects.filter(date_time_recovery__isnull=True)
        
        severity_counts = {
            'new': 0,      # < 1 hour
            'minor': 0,    # 1-2 hours
            'major': 0,    # 2-4 hours
            'critical': 0  # > 4 hours
        }
        
        for incident in active_incidents:
            color_class = get_incident_color_class(incident)
            if color_class == 'incident-new':
                severity_counts['new'] += 1
            elif color_class == 'incident-minor':
                severity_counts['minor'] += 1
            elif color_class == 'incident-major':
                severity_counts['major'] += 1
            elif color_class == 'incident-critical':
                severity_counts['critical'] += 1
        
        return {
            'total': total,
            'active': active,
            'resolved': resolved,
            'active_percentage': round((active / total * 100) if total > 0 else 0, 1),
            'resolved_percentage': round((resolved / total * 100) if total > 0 else 0, 1),
            'severity_counts': severity_counts
        }
    
    except Exception as e:
        print(f"Error calculating statistics for {network_type}: {e}")
        return {
            'total': 0,
            'active': 0,
            'resolved': 0,
            'active_percentage': 0,
            'resolved_percentage': 0,
            'severity_counts': {'new': 0, 'minor': 0, 'major': 0, 'critical': 0}
        }

def clean_string_field(value, max_length=None):
    """
    Clean and validate string fields
    """
    if not value:
        return None
    
    # Strip whitespace
    value = str(value).strip()
    
    # Check if empty after stripping
    if not value:
        return None
    
    # Truncate if too long
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    return value

def get_incident_summary_text(incident, network_type):
    """
    Generate a summary text for an incident (useful for notifications)
    """
    summary_parts = []
    
    # Add network type
    summary_parts.append(f"{network_type.replace('_', ' ').title()} Network")
    
    # Add key identifying information based on network type
    if network_type == 'transport':
        if hasattr(incident, 'extremity_a') and hasattr(incident, 'extremity_b'):
            summary_parts.append(f"({incident.extremity_a} to {incident.extremity_b})")
    elif network_type in ['file_access', 'radio_access']:
        if hasattr(incident, 'site') and hasattr(incident, 'ip_address'):
            summary_parts.append(f"Site: {incident.site} ({incident.ip_address})")
    elif network_type == 'core':
        if hasattr(incident, 'platform') and hasattr(incident, 'region_node'):
            summary_parts.append(f"{incident.platform} - {incident.region_node}")
    elif network_type == 'backbone_internet':
        if hasattr(incident, 'platform_igw') and hasattr(incident, 'link_label'):
            summary_parts.append(f"{incident.platform_igw} - {incident.link_label}")
    
    # Add duration
    duration = format_incident_duration(incident)
    summary_parts.append(f"Duration: {duration}")
    
    return " | ".join(summary_parts)