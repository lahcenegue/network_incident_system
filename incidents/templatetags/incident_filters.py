from django import template

register = template.Library()

@register.filter
def get_field_label(form, field_name):
    """Get the label for a form field"""
    if field_name in form.fields:
        return form.fields[field_name].label or field_name.replace('_', ' ').title()
    return field_name.replace('_', ' ').title()

@register.filter
def add_class(field, css_class):
    """Add CSS class to form field"""
    return field.as_widget(attrs={'class': css_class})

@register.filter
def get_incident_age_hours(incident):
    """Get incident age in hours"""
    from django.utils import timezone
    if incident.date_time_incident:
        delta = timezone.now() - incident.date_time_incident
        return round(delta.total_seconds() / 3600, 1)
    return 0