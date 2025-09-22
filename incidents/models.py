import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import validate_ipv4_address, validate_ipv6_address
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class BaseIncident(models.Model):
    """
    Base model for all incident types with common fields
    """
    # Common Fields for All Incidents
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Timestamps
    date_time_incident = models.DateTimeField(
        verbose_name="Date and time of INCIDENT",
        help_text="When the incident occurred"
    )
    date_time_recovery = models.DateTimeField(
        verbose_name="Date and time of RECOVERY",
        null=True, 
        blank=True,
        help_text="When the incident was resolved (leave empty for active incidents)"
    )
    
    # Calculated Duration
    duration_minutes = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Duration in minutes (auto-calculated)"
    )
    
    # Optional Fields (with "Other" option support)
    cause = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Root cause of the incident"
    )
    cause_other = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Other cause description (if cause is 'Other')"
    )
    
    origin = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Origin/source of the incident"
    )
    origin_other = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Other origin description (if origin is 'Other')"
    )
    
    impact_comment = models.TextField(
        verbose_name="IMPACT / COMMENT",
        blank=True,
        null=True,
        help_text="Detailed description of impact and comments"
    )
    
    # System Fields - Note: Each child model will need unique related_names
    # These will be overridden in each concrete model
    
    # Status tracking
    is_resolved = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Correction tracking (for admin review)
    correction_required = models.BooleanField(default=False)
    correction_note = models.TextField(
        blank=True,
        null=True,
        help_text="Note explaining why correction is needed (for admin review)"
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['date_time_incident']),
            models.Index(fields=['is_resolved']),
            models.Index(fields=['is_archived']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        """Override save to calculate duration and set resolution status"""
        self.calculate_duration()
        self.update_resolution_status()
        super().save(*args, **kwargs)
    
    def calculate_duration(self):
        """Calculate incident duration in minutes"""
        if self.date_time_incident:
            end_time = self.date_time_recovery or timezone.now()
            duration = end_time - self.date_time_incident
            self.duration_minutes = int(duration.total_seconds() / 60)
    
    def update_resolution_status(self):
        """Update resolution status based on recovery time"""
        self.is_resolved = bool(self.date_time_recovery)
    
    def get_duration_display(self):
        """Return human-readable duration format: 'Xd Yh Zm'"""
        if not self.duration_minutes:
            return "Calculating..."
        
        total_minutes = self.duration_minutes
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
    
    def get_severity_class(self):
        """Return CSS class based on incident age for color coding"""
        if self.is_resolved:
            return 'severity-green'
        
        if not self.date_time_incident:
            return 'severity-white'
        
        age = timezone.now() - self.date_time_incident
        hours = age.total_seconds() / 3600
        
        if hours < 1:
            return 'severity-white'
        elif hours < 2:
            return 'severity-yellow'
        elif hours < 4:
            return 'severity-orange'
        else:
            return 'severity-red'
    
    def should_auto_archive(self):
        """Check if incident should be automatically archived"""
        if not self.is_resolved or self.is_archived:
            return False
        
        # Auto-archive 2 hours after resolution if cause and origin are filled
        if self.date_time_recovery and self.cause and self.origin:
            archive_time = self.date_time_recovery + timedelta(hours=2)
            return timezone.now() >= archive_time
        
        return False
    
    def get_cause_display(self):
        """Return cause with other description if applicable"""
        if self.cause == 'Other' and self.cause_other:
            return f"Other: {self.cause_other}"
        return self.cause or "Not specified"
    
    def get_origin_display(self):
        """Return origin with other description if applicable"""
        if self.origin == 'Other' and self.origin_other:
            return f"Other: {self.origin_other}"
        return self.origin or "Not specified"
    
    def __str__(self):
        return f"Incident {str(self.id)[:8]} - {self.date_time_incident}"


def validate_ip_address(value):
    """Custom validator for both IPv4 and IPv6 addresses"""
    try:
        validate_ipv4_address(value)
    except ValidationError:
        try:
            validate_ipv6_address(value)
        except ValidationError:
            raise ValidationError("Enter a valid IPv4 or IPv6 address.")


# Network-Specific Models
class TransportNetworkIncident(BaseIncident):
    """
    Transport Networks specific incident model
    Complex SECTIONS/EQUIPMENT fields with DOT extremities
    """
    # Required Fields
    region_loop = models.CharField(
        verbose_name="REGION / LOOP",
        max_length=100,
        help_text="Select region or loop from admin-configured list"
    )
    system_capacity = models.CharField(
        verbose_name="SYSTEM / CAPACITY", 
        max_length=100,
        help_text="Select system or capacity from admin-configured list"
    )
    
    # Complex SECTIONS/EQUIPMENT fields
    dot_extremity_a = models.CharField(
        verbose_name="DOT EXTREMITY(A)",
        max_length=50,
        blank=True,
        null=True,
        help_text="DOT state for extremity A"
    )
    extremity_a = models.CharField(
        verbose_name="EXTREMITY(A)",
        max_length=200,
        help_text="Location description for extremity A"
    )
    dot_extremity_b = models.CharField(
        verbose_name="DOT EXTREMITY(B)",
        max_length=50,
        help_text="DOT state for extremity B"
    )
    extremity_b = models.CharField(
        verbose_name="EXTREMITY(B)", 
        max_length=200,
        help_text="Location description for extremity B"
    )
    
    # Responsibility (A, B, or Both)
    RESPONSIBILITY_CHOICES = [
        ('A', 'A'),
        ('B', 'B'), 
        ('Both', 'Both'),
    ]
    responsibility = models.CharField(
        verbose_name="RESPONSIBILITY",
        max_length=4,
        choices=RESPONSIBILITY_CHOICES,
        blank=True,
        null=True,
        help_text="Responsibility assignment (optional)"
    )

    # System Fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transport_incidents_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transport_incidents_updated'
    )

    class Meta:
        verbose_name = "Transport Network Incident"
        verbose_name_plural = "Transport Network Incidents"
        ordering = ['-date_time_incident']
        
    def get_location_display(self):
        """Return formatted location for display"""
        return f"{self.extremity_a} ↔ {self.extremity_b}"


class FileAccessNetworkIncident(BaseIncident):
    """
    File Access Networks specific incident model
    Includes wilaya selection and IP address validation
    """
    # Required Fields
    do_wilaya = models.CharField(
        verbose_name="DO / WILAYA",
        max_length=50,
        help_text="Select wilaya from admin-configured list"
    )
    zone_metro = models.CharField(
        verbose_name="ZONE / METRO",
        max_length=100,
        help_text="Zone or metro area identification"
    )
    site = models.CharField(
        verbose_name="SITE",
        max_length=100,
        help_text="Site identification"
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="IP Address",
        validators=[validate_ip_address],
        help_text="IPv4 or IPv6 address"
    )

    # System Fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='file_access_incidents_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='file_access_incidents_updated'
    )
    
    class Meta:
        verbose_name = "File Access Network Incident"
        verbose_name_plural = "File Access Network Incidents"
        ordering = ['-date_time_incident']
    
    def get_location_display(self):
        """Return formatted location for display"""
        return f"{self.do_wilaya} - {self.site}"


class RadioAccessNetworkIncident(BaseIncident):
    """
    Radio Access Networks specific incident model
    Similar to File Access but focused on radio sites
    """
    # Required Fields
    do_wilaya = models.CharField(
        verbose_name="DO / WILAYA",
        max_length=50,
        help_text="Select wilaya from admin-configured list"
    )
    site = models.CharField(
        verbose_name="SITE",
        max_length=100,
        help_text="Radio site identification"
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="IP ADDRESS",
        validators=[validate_ip_address],
        help_text="IPv4 or IPv6 address"
    )

    # System Fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='radio_access_incidents_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='radio_access_incidents_updated'
    )
    
    class Meta:
        verbose_name = "Radio Access Network Incident"
        verbose_name_plural = "Radio Access Network Incidents"
        ordering = ['-date_time_incident']
    
    def get_location_display(self):
        """Return formatted location for display"""
        return f"{self.do_wilaya} - {self.site}"
    
class CoreNetworkIncident(BaseIncident):
    """
    Core Networks specific incident model
    Platform and region-based with optional SECTIONS/EQUIPMENT
    """
    # Required Fields
    platform = models.CharField(
        verbose_name="PLATFORM",
        max_length=100,
        help_text="Select platform from admin-configured list"
    )
    region_node = models.CharField(
        verbose_name="REGION / NODE",
        max_length=100,
        help_text="Select region or node from admin-configured list"
    )
    
    # Optional Site Field
    site = models.CharField(
        verbose_name="SITE",
        max_length=100,
        blank=True,
        null=True,
        help_text="Site identification (optional)"
    )
    
    # Optional Complex SECTIONS/EQUIPMENT fields (similar to Transport)
    dot_extremity_a = models.CharField(
        verbose_name="DOT EXTREMITY(A)",
        max_length=50,
        blank=True,
        null=True,
        help_text="DOT state for extremity A"
    )
    extremity_a = models.CharField(
        verbose_name="EXTREMITY(A)",
        max_length=200,
        blank=True,
        null=True,
        help_text="Location description for extremity A"
    )
    dot_extremity_b = models.CharField(
        verbose_name="DOT EXTREMITY(B)",
        max_length=50,
        blank=True,
        null=True,
        help_text="DOT state for extremity B"
    )
    extremity_b = models.CharField(
        verbose_name="EXTREMITY(B)",
        max_length=200,
        blank=True,
        null=True,
        help_text="Location description for extremity B"
    )

    # System Fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='core_incidents_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='core_incidents_updated'
    )
    
    class Meta:
        verbose_name = "Core Network Incident"
        verbose_name_plural = "Core Network Incidents"
        ordering = ['-date_time_incident']
    
    def get_location_display(self):
        """Return formatted location for display"""
        if self.extremity_a and self.extremity_b:
            return f"{self.extremity_a} ↔ {self.extremity_b}"
        elif self.site:
            return f"{self.region_node} - {self.site}"
        else:
            return self.region_node


class BackboneInternetNetworkIncident(BaseIncident):
    """
    Backbone Internet Networks specific incident model
    Interconnect type and platform/IGW focused
    """
    # Required Fields
    interconnect_type = models.CharField(
        verbose_name="INTERCONNECT TYPE",
        max_length=100,
        help_text="Select interconnect type from admin-configured list"
    )
    platform_igw = models.CharField(
        verbose_name="PLATFORM/IGW",
        max_length=100,
        help_text="Select platform or IGW from admin-configured list"
    )
    link_label = models.CharField(
        verbose_name="LINK LABEL",
        max_length=200,
        help_text="Link name or label identification"
    )

    # System Fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='backbone_incidents_created'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='backbone_incidents_updated'
    )
    
    class Meta:
        verbose_name = "Backbone Internet Network Incident"
        verbose_name_plural = "Backbone Internet Network Incidents"
        ordering = ['-date_time_incident']
    
    def get_location_display(self):
        """Return formatted location for display"""
        return f"{self.platform_igw} - {self.link_label}"


# Configuration Models for Admin Panel Dropdown Management
class DropdownConfiguration(models.Model):
    """
    Base model for managing dropdown list values in admin panel
    """
    category = models.CharField(
        max_length=50,
        help_text="Configuration category (e.g., 'transport_regions', 'wilayas')"
    )
    value = models.CharField(
        max_length=200,
        help_text="Display value for dropdown option"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this option is available for selection"
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Dropdown Configuration"
        verbose_name_plural = "Dropdown Configurations"
        ordering = ['category', 'sort_order', 'value']
        unique_together = ('category', 'value')
    
    def __str__(self):
        return f"{self.category}: {self.value}"


class AuditLog(models.Model):
    """
    Audit trail for all system changes
    """
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('VIEW', 'View'),
        ('EXPORT', 'Export'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who performed the action"
    )
    action = models.CharField(
        max_length=10,
        choices=ACTION_CHOICES,
        help_text="Type of action performed"
    )
    model_name = models.CharField(
        max_length=50,
        help_text="Name of the model affected"
    )
    object_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID of the affected object"
    )
    changes = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON representation of changes made"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="Browser user agent string"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the action occurred"
    )
    
    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['model_name', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} at {self.timestamp}"


class SystemConfiguration(models.Model):
    """
    System-wide configuration settings
    """
    key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Configuration key identifier"
    )
    value = models.TextField(
        help_text="Configuration value (JSON for complex data)"
    )
    description = models.CharField(
        max_length=255,
        help_text="Human-readable description of this setting"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this configuration is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configurations"
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.description}"


# Utility function for model managers
class ActiveIncidentManager(models.Manager):
    """Manager for active (non-resolved) incidents"""
    def get_queryset(self):
        return super().get_queryset().filter(is_resolved=False, is_archived=False)


class ArchivedIncidentManager(models.Manager):
    """Manager for archived incidents"""
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=True)


class ResolvedIncidentManager(models.Manager):
    """Manager for resolved incidents"""
    def get_queryset(self):
        return super().get_queryset().filter(is_resolved=True)


# Add custom managers to incident models
def add_custom_managers():
    """Function to add custom managers to all incident models"""
    incident_models = [
        TransportNetworkIncident,
        FileAccessNetworkIncident,
        RadioAccessNetworkIncident,
        CoreNetworkIncident,
        BackboneInternetNetworkIncident,
    ]
    
    for model in incident_models:
        model.add_to_class('objects', models.Manager())  # Default manager
        model.add_to_class('active', ActiveIncidentManager())  # Active incidents
        model.add_to_class('archived', ArchivedIncidentManager())  # Archived incidents
        model.add_to_class('resolved', ResolvedIncidentManager())  # Resolved incidents


# Call the function to add managers
add_custom_managers()


# Signal handlers for automatic archival and audit logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver


@receiver(post_save, sender=TransportNetworkIncident)
@receiver(post_save, sender=FileAccessNetworkIncident)
@receiver(post_save, sender=RadioAccessNetworkIncident)
@receiver(post_save, sender=CoreNetworkIncident)
@receiver(post_save, sender=BackboneInternetNetworkIncident)
def incident_post_save_handler(sender, instance, created, **kwargs):
    """
    Handle post-save operations for incidents
    - Create audit log entry
    - Check for automatic archival
    """
    # Create audit log entry
    action = 'CREATE' if created else 'UPDATE'
    AuditLog.objects.create(
        user=getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None),
        action=action,
        model_name=sender.__name__,
        object_id=str(instance.id),
        # We'll add change tracking in a future enhancement
    )
    
    # Check for automatic archival
    if instance.should_auto_archive():
        instance.is_archived = True
        instance.archived_at = timezone.now()
        instance.save(update_fields=['is_archived', 'archived_at'])