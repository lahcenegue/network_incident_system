from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def incident_severity_class(incident):
    """
    Return CSS class based on incident duration for color coding
    White: < 1 hour
    Yellow: 1-2 hours
    Orange: 2-4 hours
    Red: > 4 hours
    Green: resolved
    """
    if incident.date_time_recovery:
        return 'severity-green'  # Resolved
    
    now = timezone.now()
    duration = now - incident.date_time_incident
    
    if duration < timedelta(hours=1):
        return 'severity-white'
    elif duration < timedelta(hours=2):
        return 'severity-yellow'
    elif duration < timedelta(hours=4):
        return 'severity-orange'
    else:
        return 'severity-red'

@register.filter
def incident_duration_text(incident):
    """
    Return human-readable duration text
    """
    if incident.date_time_recovery:
        duration = incident.date_time_recovery - incident.date_time_incident
    else:
        duration = timezone.now() - incident.date_time_incident
    
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"