# incidents/templatetags/incident_tags.py
from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe
import math

register = template.Library()

@register.filter
def severity_class(incident):
    """
    Return CSS class based on incident severity/age
    Usage: {{ incident|severity_class }}
    """
    if hasattr(incident, 'get_severity_class'):
        return incident.get_severity_class()
    return 'incident-new'

@register.filter
def severity_display(incident):
    """
    Return human-readable severity level
    Usage: {{ incident|severity_display }}
    """
    if hasattr(incident, 'get_severity_display'):
        return incident.get_severity_display()
    return 'New'

@register.filter
def duration_display(incident):
    """
    Return formatted duration display
    Usage: {{ incident|duration_display }}
    """
    if hasattr(incident, 'get_duration_display'):
        return incident.get_duration_display()
    return '0m'

@register.filter
def age_in_hours(incident):
    """
    Return incident age in hours
    Usage: {{ incident|age_in_hours }}
    """
    if hasattr(incident, 'get_age_in_hours'):
        return round(incident.get_age_in_hours(), 1)
    return 0

@register.simple_tag
def severity_badge(incident):
    """
    Return HTML for severity badge
    Usage: {% severity_badge incident %}
    """
    if not incident:
        return ''
    
    severity = incident.get_severity_display() if hasattr(incident, 'get_severity_display') else 'New'
    css_class = incident.get_severity_class() if hasattr(incident, 'get_severity_class') else 'incident-new'
    
    # Map CSS classes to badge classes
    badge_class_map = {
        'incident-new': 'new',
        'incident-low': 'low', 
        'incident-medium': 'medium',
        'incident-critical': 'critical',
        'incident-resolved': 'resolved'
    }
    
    badge_class = badge_class_map.get(css_class, 'new')
    
    html = f'<span class="severity-badge {badge_class}">{severity}</span>'
    return mark_safe(html)

@register.simple_tag
def age_indicator(incident):
    """
    Return HTML for age indicator dot
    Usage: {% age_indicator incident %}
    """
    if not incident:
        return ''
    
    css_class = incident.get_severity_class() if hasattr(incident, 'get_severity_class') else 'incident-new'
    
    # Map CSS classes to indicator classes
    indicator_class_map = {
        'incident-new': 'new',
        'incident-low': 'low',
        'incident-medium': 'medium', 
        'incident-critical': 'critical',
        'incident-resolved': 'resolved'
    }
    
    indicator_class = indicator_class_map.get(css_class, 'new')
    
    html = f'<span class="incident-age-indicator {indicator_class}"></span>'
    return mark_safe(html)

@register.simple_tag
def status_icon(incident):
    """
    Return HTML for status icon
    Usage: {% status_icon incident %}
    """
    if not incident:
        return ''
    
    css_class = incident.get_severity_class() if hasattr(incident, 'get_severity_class') else 'incident-new'
    
    # Map CSS classes to icons and colors
    icon_map = {
        'incident-new': ('bi-circle', 'new'),
        'incident-low': ('bi-exclamation-triangle', 'low'),
        'incident-medium': ('bi-exclamation-triangle-fill', 'medium'),
        'incident-critical': ('bi-exclamation-octagon-fill', 'critical'),
        'incident-resolved': ('bi-check-circle-fill', 'resolved')
    }
    
    icon, color_class = icon_map.get(css_class, ('bi-circle', 'new'))
    
    html = f'<i class="bi {icon} status-icon {color_class}"></i>'
    return mark_safe(html)

@register.inclusion_tag('incidents/severity_legend.html')
def severity_legend():
    """
    Render severity legend
    Usage: {% severity_legend %}
    """
    legend_items = [
        {'class': 'new', 'label': 'New (< 1 hour)', 'description': 'Recently reported incidents'},
        {'class': 'low', 'label': 'Low (1-2 hours)', 'description': 'Incidents requiring attention'},
        {'class': 'medium', 'label': 'Medium (2-4 hours)', 'description': 'Incidents needing urgent response'},
        {'class': 'critical', 'label': 'Critical (> 4 hours)', 'description': 'Critical incidents requiring immediate action'},
        {'class': 'resolved', 'label': 'Resolved', 'description': 'Completed incidents'},
    ]
    return {'legend_items': legend_items}

@register.filter
def time_since(incident_time):
    """
    Return human-readable time since incident
    Usage: {{ incident.date_time_incident|time_since }}
    """
    if not incident_time:
        return 'Unknown'
    
    now = timezone.now()
    if incident_time > now:
        return 'In the future'
    
    diff = now - incident_time
    total_seconds = diff.total_seconds()
    
    if total_seconds < 60:
        return f"{int(total_seconds)} seconds ago"
    elif total_seconds < 3600:  # Less than 1 hour
        minutes = int(total_seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif total_seconds < 86400:  # Less than 1 day
        hours = int(total_seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:  # Days
        days = int(total_seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"

@register.filter
def format_duration(total_minutes):
    """
    Format duration in minutes to human readable format
    Usage: {{ incident.duration_minutes|format_duration }}
    """
    if not total_minutes or total_minutes <= 0:
        return "0m"
    
    days = total_minutes // (24 * 60)
    hours = (total_minutes % (24 * 60)) // 60
    minutes = total_minutes % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    
    return " ".join(parts) if parts else "0m"

@register.simple_tag
def incident_summary_card(incidents, severity_class):
    """
    Generate summary card HTML for incidents of specific severity
    Usage: {% incident_summary_card incidents 'critical' %}
    """
    if not incidents:
        return ''
    
    # Filter incidents by severity
    filtered_incidents = [
        incident for incident in incidents 
        if hasattr(incident, 'get_severity_class') and 
        incident.get_severity_class() == f'incident-{severity_class}'
    ]
    
    count = len(filtered_incidents)
    
    severity_labels = {
        'new': 'New',
        'low': 'Low Priority', 
        'medium': 'Medium Priority',
        'critical': 'Critical',
        'resolved': 'Resolved'
    }
    
    label = severity_labels.get(severity_class, severity_class.title())
    
    html = f'''
    <div class="severity-summary-card {severity_class}">
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <h6 class="mb-0">{label}</h6>
                <small class="text-muted">{count} incident{'s' if count != 1 else ''}</small>
            </div>
            <div class="h3 mb-0">{count}</div>
        </div>
    </div>
    '''
    
    return mark_safe(html)

@register.filter
def get_network_type(incident):
    """
    Get network type from incident class name
    Usage: {{ incident|get_network_type }}
    """
    if hasattr(incident, 'get_network_type'):
        return incident.get_network_type()
    
    class_name = incident.__class__.__name__
    if 'Transport' in class_name:
        return 'Transport Networks'
    elif 'FileAccess' in class_name:
        return 'File Access Networks'
    elif 'RadioAccess' in class_name:
        return 'Radio Access Networks'
    elif 'Core' in class_name:
        return 'Core Networks'
    elif 'BackboneInternet' in class_name:
        return 'Backbone Internet Networks'
    return 'Unknown Network'

@register.filter
def truncate_id(uuid_string, length=8):
    """
    Truncate UUID to shorter display format
    Usage: {{ incident.id|truncate_id }}
    """
    if not uuid_string:
        return ''
    return str(uuid_string)[:length]