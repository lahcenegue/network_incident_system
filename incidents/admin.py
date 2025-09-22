from django.contrib import admin
from .models import (
    TransportNetworkIncident,
    FileAccessNetworkIncident,
    RadioAccessNetworkIncident,
    CoreNetworkIncident,
    BackboneInternetNetworkIncident,
    DropdownConfiguration,
    AuditLog,
    SystemConfiguration
)

@admin.register(TransportNetworkIncident)
class TransportNetworkIncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'region_loop', 'get_location_display', 'date_time_incident', 'is_resolved', 'get_duration_display')
    list_filter = ('is_resolved', 'is_archived', 'region_loop', 'created_at')
    search_fields = ('region_loop', 'system_capacity', 'extremity_a', 'extremity_b')
    readonly_fields = ('id', 'duration_minutes', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('region_loop', 'system_capacity')
        }),
        ('Location Details', {
            'fields': ('dot_extremity_a', 'extremity_a', 'dot_extremity_b', 'extremity_b', 'responsibility')
        }),
        ('Timing', {
            'fields': ('date_time_incident', 'date_time_recovery', 'duration_minutes')
        }),
        ('Incident Details', {
            'fields': ('cause', 'cause_other', 'origin', 'origin_other', 'impact_comment')
        }),
        ('System Fields', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at', 'is_resolved', 'is_archived'),
            'classes': ('collapse',)
        })
    )

@admin.register(FileAccessNetworkIncident)
class FileAccessNetworkIncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'do_wilaya', 'site', 'ip_address', 'date_time_incident', 'is_resolved', 'get_duration_display')
    list_filter = ('is_resolved', 'is_archived', 'do_wilaya', 'created_at')
    search_fields = ('do_wilaya', 'zone_metro', 'site', 'ip_address')
    readonly_fields = ('id', 'duration_minutes', 'created_at', 'updated_at')

@admin.register(RadioAccessNetworkIncident)
class RadioAccessNetworkIncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'do_wilaya', 'site', 'ip_address', 'date_time_incident', 'is_resolved', 'get_duration_display')
    list_filter = ('is_resolved', 'is_archived', 'do_wilaya', 'created_at')
    search_fields = ('do_wilaya', 'site', 'ip_address')
    readonly_fields = ('id', 'duration_minutes', 'created_at', 'updated_at')

@admin.register(CoreNetworkIncident)
class CoreNetworkIncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'platform', 'region_node', 'site', 'date_time_incident', 'is_resolved', 'get_duration_display')
    list_filter = ('is_resolved', 'is_archived', 'platform', 'created_at')
    search_fields = ('platform', 'region_node', 'site', 'extremity_a', 'extremity_b')
    readonly_fields = ('id', 'duration_minutes', 'created_at', 'updated_at')

@admin.register(BackboneInternetNetworkIncident)
class BackboneInternetNetworkIncidentAdmin(admin.ModelAdmin):
    list_display = ('id', 'interconnect_type', 'platform_igw', 'link_label', 'date_time_incident', 'is_resolved', 'get_duration_display')
    list_filter = ('is_resolved', 'is_archived', 'interconnect_type', 'created_at')
    search_fields = ('interconnect_type', 'platform_igw', 'link_label')
    readonly_fields = ('id', 'duration_minutes', 'created_at', 'updated_at')

@admin.register(DropdownConfiguration)
class DropdownConfigurationAdmin(admin.ModelAdmin):
    list_display = ('category', 'value', 'is_active', 'sort_order')
    list_filter = ('category', 'is_active')
    search_fields = ('category', 'value')
    list_editable = ('is_active', 'sort_order')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'model_name', 'object_id', 'ip_address')
    list_filter = ('action', 'model_name', 'timestamp')
    search_fields = ('user__username', 'model_name', 'object_id')
    readonly_fields = ('timestamp', 'user', 'action', 'model_name', 'object_id', 'changes', 'ip_address', 'user_agent')
    
    def has_add_permission(self, request):
        return False  # Audit logs should not be manually created
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should not be modified
    
    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs should not be deleted

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'description', 'is_active', 'updated_at')
    list_filter = ('is_active', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')