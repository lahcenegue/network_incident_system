# incidents/models.py
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import validate_ipv4_address, validate_ipv6_address
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

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
    
    # Status tracking
    is_resolved = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)
    
    # Audit fields - User tracking and timestamps
    created_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='%(class)s_created',
        help_text="User who created this incident"
    )
    updated_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        help_text="User who last updated this incident"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Historical archival fields
    archived_by = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_archived',
        help_text="User who archived this incident"
    )
    
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
            
            # NEW: Composite indexes for performance optimization
            models.Index(fields=['is_resolved', 'date_time_incident']),  # For active/resolved filtering with date sorting
            models.Index(fields=['date_time_incident', 'is_resolved']),  # For date range queries with status
            models.Index(fields=['cause', 'date_time_incident']),        # For cause filtering with date sorting
            models.Index(fields=['origin', 'date_time_incident']),       # For origin filtering with date sorting
            models.Index(fields=['created_by', 'date_time_incident']),   # For user-specific queries
            
            # Index for auto-archival queries
            models.Index(fields=['is_resolved', 'date_time_recovery', 'cause', 'origin']),
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
        if not self.date_time_incident:
            return "Not started"
        
        # Calculate current duration if not resolved
        if not self.is_resolved:
            current_time = timezone.now()
            duration = current_time - self.date_time_incident
            total_minutes = max(0, int(duration.total_seconds() / 60))
        else:
            total_minutes = self.duration_minutes or 0
        
        if total_minutes == 0:
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
    
    def get_severity_class(self):
        """Return CSS class based on incident age for color coding"""
        if self.is_resolved:
            return 'incident-resolved'
        
        if not self.date_time_incident:
            return 'incident-new'
        
        # Calculate hours since incident started
        age = timezone.now() - self.date_time_incident
        hours = age.total_seconds() / 3600
        
        if hours < 1:
            return 'incident-new'      # White background
        elif hours < 2:
            return 'incident-low'      # Yellow background
        elif hours < 4:
            return 'incident-medium'   # Orange background
        else:
            return 'incident-critical' # Red background
    
    def get_severity_display(self):
        """Return human-readable severity level"""
        if self.is_resolved:
            return "Resolved"
        
        if not self.date_time_incident:
            return "New"
        
        age = timezone.now() - self.date_time_incident
        hours = age.total_seconds() / 3600
        
        if hours < 1:
            return "New"
        elif hours < 2:
            return "Low Severity"
        elif hours < 4:
            return "Medium Severity"
        else:
            return "Critical"
    
    def get_age_in_hours(self):
        """Return incident age in hours as float"""
        if not self.date_time_incident:
            return 0
        
        if self.is_resolved and self.date_time_recovery:
            age = self.date_time_recovery - self.date_time_incident
        else:
            age = timezone.now() - self.date_time_incident
        
        return max(0, age.total_seconds() / 3600)
    
    def should_auto_archive(self):
        """Check if incident should be automatically archived"""
        if not self.is_resolved or self.is_archived:
            return False
        
        # Auto-archive 2 hours after resolution if cause and origin are filled
        if (self.date_time_recovery and 
            self.cause and self.cause.strip() and
            self.origin and self.origin.strip()):
            archive_time = self.date_time_recovery + timedelta(hours=2)
            return timezone.now() >= archive_time
        
        return False
    
    def can_be_archived(self):
        """
        Check if incident meets ALL criteria for archival.
        
        CRITICAL BUSINESS RULES:
        1. Must be resolved (date_time_recovery is not null)
        2. Must have cause field filled (not empty/null)
        3. Must have origin field filled (not empty/null)
        4. At least 2 hours must have passed since resolution
        5. Must not already be archived
        
        Returns:
            bool: True if incident can be archived, False otherwise
        """
        # Check if incident is resolved
        if not self.date_time_recovery:
            return False
        
        # Check if cause is filled (REQUIRED for archival)
        if not self.cause or self.cause.strip() == '':
            return False
        
        # Check if origin is filled (REQUIRED for archival)
        if not self.origin or self.origin.strip() == '':
            return False
        
        # Check if already archived
        if self.is_archived:
            return False
        
        # Check if 2 hours have passed since resolution
        time_since_resolution = timezone.now() - self.date_time_recovery
        if time_since_resolution < timedelta(hours=2):
            return False
        
        return True
    
    def archive(self, user):
        """
        Archive this incident.
        
        This method marks the incident as archived and records who archived it
        and when. It should only be called after verifying can_be_archived() 
        returns True.
        
        Args:
            user: The CustomUser object performing the archival
            
        Returns:
            bool: True if archived successfully, False otherwise
            
        Raises:
            ValueError: If incident cannot be archived
        """
        if not self.can_be_archived():
            raise ValueError(
                "Incident cannot be archived. Ensure it is resolved, "
                "has cause and origin filled, and 2+ hours have passed since resolution."
            )
        
        try:
            self.is_archived = True
            self.archived_at = timezone.now()
            self.archived_by = user
            self.updated_by = user
            self.save(update_fields=['is_archived', 'archived_at', 'archived_by', 'updated_by', 'updated_at'])
            return True
        except Exception as e:
            # Log the error (you can enhance this with proper logging later)
            print(f"Error archiving incident {self.id}: {str(e)}")
            return False
    
    def restore(self, user):
        """
        Restore this incident from archived state.
        
        This method unarchives an incident, clearing the archived status
        and updating the audit trail.
        
        Args:
            user: The CustomUser object performing the restoration
            
        Returns:
            bool: True if restored successfully, False otherwise
        """
        if not self.is_archived:
            return False  # Already active, nothing to restore
        
        try:
            self.is_archived = False
            self.archived_at = None
            self.archived_by = None
            self.updated_by = user
            self.save(update_fields=['is_archived', 'archived_at', 'archived_by', 'updated_by', 'updated_at'])
            return True
        except Exception as e:
            # Log the error (you can enhance this with proper logging later)
            print(f"Error restoring incident {self.id}: {str(e)}")
            return False
    
    def get_cause_display(self):
        """Return cause with other description if applicable"""
        if not self.cause:
            return "Not specified"
        
        if self.cause.lower() == 'other' and self.cause_other:
            return f"Other: {self.cause_other}"
        return self.cause
    
    def get_origin_display(self):
        """Return origin with other description if applicable"""
        if not self.origin:
            return "Not specified"
        
        if self.origin.lower() == 'other' and self.origin_other:
            return f"Other: {self.origin_other}"
        return self.origin
    
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
        ('', '--- None ---'),
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
        'authentication.CustomUser', 
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