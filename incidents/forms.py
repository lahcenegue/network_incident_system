from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    TransportNetworkIncident, FileAccessNetworkIncident,
    RadioAccessNetworkIncident, CoreNetworkIncident,
    BackboneInternetNetworkIncident, DropdownConfiguration
)
from .validators import IncidentValidators, DuplicateIncidentChecker
import ipaddress
from datetime import timedelta

class BaseIncidentForm(forms.ModelForm):
    """Base form with common validation for all incident types"""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Enhanced datetime widgets with 24-hour format enforcement
        if 'date_time_incident' in self.fields:
            self.fields['date_time_incident'].widget = forms.DateTimeInput(attrs={
                'class': 'form-control datetime-24h',
                'type': 'datetime-local',
                'step': '60',
                'data-format': '24',
                'pattern': '[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}',
                'title': 'Select date and time when the incident occurred (24-hour format)'
            })
            # Set default to current time for new incidents
            if not self.instance.pk:
                now = timezone.now()
                # Format for datetime-local input in 24-hour format
                self.fields['date_time_incident'].initial = now.strftime('%Y-%m-%dT%H:%M')

        if 'date_time_recovery' in self.fields:
            self.fields['date_time_recovery'].widget = forms.DateTimeInput(attrs={
                'class': 'form-control datetime-24h',
                'type': 'datetime-local', 
                'step': '60',
                'pattern': '[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}',
                'title': 'Select date and time when the incident was resolved (24-hour format, leave empty if still active)'
            })
            self.fields['date_time_recovery'].required = False
        
        # POPULATE DROPDOWN CHOICES IMMEDIATELY
        self._populate_dropdown_choices()

    def _populate_dropdown_choices(self):
        """Populate dropdown choices from database"""
        try:
            from .models import DropdownConfiguration
            
            # Populate common choices
            if 'cause' in self.fields:
                cause_choices = [('', '--- Select Cause ---')]
                causes = DropdownConfiguration.objects.filter(
                    category='cause', is_active=True
                ).order_by('sort_order', 'value')
                cause_choices.extend([(c.value, c.value) for c in causes])
                self.fields['cause'].choices = cause_choices
            
            if 'origin' in self.fields:
                origin_choices = [('', '--- Select Origin ---')]
                origins = DropdownConfiguration.objects.filter(
                    category='origin', is_active=True
                ).order_by('sort_order', 'value')
                origin_choices.extend([(o.value, o.value) for o in origins])
                self.fields['origin'].choices = origin_choices
                
        except Exception as e:
            print(f"Error populating common dropdown choices: {e}")
    
    def clean_date_time_incident(self):
        """Enhanced validation for incident time"""
        incident_time = self.cleaned_data.get('date_time_incident')
        if incident_time:
            now = timezone.now()
            
            # Check if incident time is in the future (max 1 hour ahead)
            max_future = now + timedelta(hours=1)
            if incident_time > max_future:
                raise forms.ValidationError(
                    "Incident time cannot be more than 1 hour in the future"
                )
            
            # Check if incident time is too far in the past (max 1 year)
            max_past = now - timedelta(days=365)
            if incident_time < max_past:
                raise forms.ValidationError(
                    "Incident time cannot be more than 1 year in the past"
                )
                
        return incident_time
    
    def clean_date_time_recovery(self):
        """Enhanced validation for recovery time"""
        recovery_time = self.cleaned_data.get('date_time_recovery')
        if recovery_time:
            now = timezone.now()
            
            # Recovery time cannot be in the future
            if recovery_time > now:
                raise forms.ValidationError(
                    "Recovery time cannot be in the future"
                )
        
        return recovery_time
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        incident_time = cleaned_data.get('date_time_incident')
        recovery_time = cleaned_data.get('date_time_recovery')
        
        # Validate recovery time if provided
        if incident_time and recovery_time:
            if recovery_time <= incident_time:
                raise forms.ValidationError(
                    "Recovery time must be after the incident time"
                )
            
            # Check if recovery is too long after incident (max 30 days)
            max_duration = incident_time + timedelta(days=30)
            if recovery_time > max_duration:
                raise forms.ValidationError(
                    "Recovery time cannot be more than 30 days after incident time"
                )
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            if not instance.pk:  # New instance
                instance.created_by = self.user
            instance.updated_by = self.user
        
        if commit:
            instance.save()
        return instance

class TransportNetworkIncidentForm(BaseIncidentForm):
    """Form for Transport Network Incidents with advanced validation"""
    
    class Meta:
        model = TransportNetworkIncident
        fields = [
            'region_loop', 'system_capacity', 'dot_extremity_a', 'extremity_a',
            'dot_extremity_b', 'extremity_b', 'responsibility',
            'date_time_incident', 'date_time_recovery', 'cause', 'origin', 'impact_comment'
        ]
        widgets = {
            'region_loop': forms.Select(attrs={'class': 'form-select'}),
            'system_capacity': forms.Select(attrs={'class': 'form-select'}),
            'dot_extremity_a': forms.Select(attrs={'class': 'form-select'}),
            'extremity_a': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter extremity A location'}),
            'dot_extremity_b': forms.Select(attrs={'class': 'form-select'}),
            'extremity_b': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter extremity B location'}),
            'responsibility': forms.Select(attrs={'class': 'form-select'}),
            'cause': forms.Select(attrs={'class': 'form-select'}),
            'origin': forms.Select(attrs={'class': 'form-select'}),
            'impact_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the impact and any additional comments...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._populate_transport_choices()

    def _populate_transport_choices(self):
        """Populate transport-specific choices"""
        try:
            from .models import DropdownConfiguration
            
            if 'region_loop' in self.fields:
                choices = [('', '--- Select Region/Loop ---')]
                configs = DropdownConfiguration.objects.filter(
                    category='region_loop', is_active=True
                ).order_by('sort_order', 'value')
                choices.extend([(c.value, c.value) for c in configs])
                self.fields['region_loop'].choices = choices
            
            if 'system_capacity' in self.fields:
                choices = [('', '--- Select System/Capacity ---')]
                configs = DropdownConfiguration.objects.filter(
                    category='system_capacity', is_active=True
                ).order_by('sort_order', 'value')
                choices.extend([(c.value, c.value) for c in configs])
                self.fields['system_capacity'].choices = choices
            
            if 'dot_extremity_a' in self.fields:
                choices = [('', '--- Select DOT State ---')]
                configs = DropdownConfiguration.objects.filter(
                    category='dot_states', is_active=True
                ).order_by('sort_order', 'value')
                choices.extend([(c.value, c.value) for c in configs])
                self.fields['dot_extremity_a'].choices = choices
                self.fields['dot_extremity_b'].choices = choices
            
            # Add responsibility choices
            if 'responsibility' in self.fields:
                self.fields['responsibility'].choices = [
                    ('', '--- Select Responsibility ---'),
                    ('A', 'A'),
                    ('B', 'B'),
                    ('Both', 'Both'),
                ]
                
        except Exception as e:
            print(f"Error populating transport choices: {e}")
    
    def clean(self):
        cleaned_data = super().clean()
        extremity_a = cleaned_data.get('extremity_a')
        extremity_b = cleaned_data.get('extremity_b')
        dot_extremity_a = cleaned_data.get('dot_extremity_a')
        dot_extremity_b = cleaned_data.get('dot_extremity_b')
        incident_time = cleaned_data.get('date_time_incident')
        
        # Validate extremity consistency
        if extremity_a and not dot_extremity_a:
            raise forms.ValidationError("DOT Extremity A is required when Extremity A is provided")
        
        if extremity_b and not dot_extremity_b:
            raise forms.ValidationError("DOT Extremity B is required when Extremity B is provided")
        
        if extremity_a and extremity_b and extremity_a.strip().lower() == extremity_b.strip().lower():
            raise forms.ValidationError("Extremity A and Extremity B cannot be the same location")
        
        # Check for duplicates (only for new incidents)
        if not self.instance.pk and extremity_a and extremity_b and incident_time:
            existing = TransportNetworkIncident.objects.filter(
                extremity_a__iexact=extremity_a,
                extremity_b__iexact=extremity_b,
                date_time_incident__gte=incident_time - timedelta(hours=1),
                date_time_incident__lte=incident_time + timedelta(hours=1),
                date_time_recovery__isnull=True
            )
            if existing.exists():
                raise forms.ValidationError(
                    f"A similar incident for {extremity_a} to {extremity_b} already exists within the last hour"
                )
        
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._populate_transport_choices()

    def _populate_transport_choices(self):
        """Populate transport-specific choices"""
        try:
            from .models import DropdownConfiguration
            
            if 'region_loop' in self.fields:
                choices = [('', '--- Select Region/Loop ---')]
                configs = DropdownConfiguration.objects.filter(
                    category='region_loop', is_active=True
                ).order_by('sort_order', 'value')
                choices.extend([(c.value, c.value) for c in configs])
                self.fields['region_loop'].choices = choices
            
            if 'system_capacity' in self.fields:
                choices = [('', '--- Select System/Capacity ---')]
                configs = DropdownConfiguration.objects.filter(
                    category='system_capacity', is_active=True
                ).order_by('sort_order', 'value')
                choices.extend([(c.value, c.value) for c in configs])
                self.fields['system_capacity'].choices = choices
            
            if 'dot_extremity_a' in self.fields:
                choices = [('', '--- Select DOT State ---')]
                configs = DropdownConfiguration.objects.filter(
                    category='dot_states', is_active=True
                ).order_by('sort_order', 'value')
                choices.extend([(c.value, c.value) for c in configs])
                self.fields['dot_extremity_a'].choices = choices
                self.fields['dot_extremity_b'].choices = choices
                
        except Exception as e:
            print(f"Error populating transport choices: {e}")

class FileAccessNetworkIncidentForm(BaseIncidentForm):
    """Form for File Access Network Incidents with IP validation"""
    
    class Meta:
        model = FileAccessNetworkIncident
        fields = [
            'do_wilaya', 'zone_metro', 'site', 'ip_address',
            'date_time_incident', 'date_time_recovery', 'cause', 'origin', 'impact_comment'
        ]
        widgets = {
            'do_wilaya': forms.Select(attrs={'class': 'form-select'}),
            'zone_metro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter zone/metro area'}),
            'site': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter site identification'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter IP address (e.g., 192.168.1.1)'}),
            'cause': forms.Select(attrs={'class': 'form-select'}),
            'origin': forms.Select(attrs={'class': 'form-select'}),
            'impact_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the impact and any additional comments...'}),
        }
    
    def clean_ip_address(self):
        """Validate IP address format"""
        ip_address = self.cleaned_data.get('ip_address')
        if ip_address:
            try:
                ipaddress.ip_address(ip_address)
            except ValueError:
                raise forms.ValidationError(f"'{ip_address}' is not a valid IP address format")
        return ip_address
    
    def clean_site(self):
        """Validate site name"""
        site = self.cleaned_data.get('site')
        if site:
            site = site.strip()
            if len(site) < 2:
                raise forms.ValidationError("Site name must be at least 2 characters long")
            if len(site) > 50:
                raise forms.ValidationError("Site name cannot exceed 50 characters")
        return site

class RadioAccessNetworkIncidentForm(BaseIncidentForm):
    """Form for Radio Access Network Incidents"""
    
    class Meta:
        model = RadioAccessNetworkIncident
        fields = [
            'do_wilaya', 'site', 'ip_address',
            'date_time_incident', 'date_time_recovery', 'cause', 'origin', 'impact_comment'
        ]
        widgets = {
            'do_wilaya': forms.Select(attrs={'class': 'form-select'}),
            'site': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter site identification'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter IP address (e.g., 192.168.1.1)'}),
            'cause': forms.Select(attrs={'class': 'form-select'}),
            'origin': forms.Select(attrs={'class': 'form-select'}),
            'impact_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the impact and any additional comments...'}),
        }
    
    def clean_ip_address(self):
        """Validate IP address format"""
        ip_address = self.cleaned_data.get('ip_address')
        if ip_address:
            try:
                ipaddress.ip_address(ip_address)
            except ValueError:
                raise forms.ValidationError(f"'{ip_address}' is not a valid IP address format")
        return ip_address

class CoreNetworkIncidentForm(BaseIncidentForm):
    """Form for Core Network Incidents"""
    
    class Meta:
        model = CoreNetworkIncident
        fields = [
            'platform', 'region_node', 'site', 'dot_extremity_a', 'extremity_a',
            'dot_extremity_b', 'extremity_b', 'date_time_incident', 'date_time_recovery',
            'cause', 'origin', 'impact_comment'
        ]
        widgets = {
            'platform': forms.Select(attrs={'class': 'form-select'}),
            'region_node': forms.Select(attrs={'class': 'form-select'}),
            'site': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter site (optional)'}),
            'dot_extremity_a': forms.Select(attrs={'class': 'form-select'}),
            'extremity_a': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter extremity A location'}),
            'dot_extremity_b': forms.Select(attrs={'class': 'form-select'}),
            'extremity_b': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter extremity B location'}),
            'cause': forms.Select(attrs={'class': 'form-select'}),
            'origin': forms.Select(attrs={'class': 'form-select'}),
            'impact_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the impact and any additional comments...'}),
        }

class BackboneInternetNetworkIncidentForm(BaseIncidentForm):
    """Form for Backbone Internet Network Incidents"""
    
    class Meta:
        model = BackboneInternetNetworkIncident
        fields = [
            'interconnect_type', 'platform_igw', 'link_label',
            'date_time_incident', 'date_time_recovery', 'cause', 'origin', 'impact_comment'
        ]
        widgets = {
            'interconnect_type': forms.Select(attrs={'class': 'form-select'}),
            'platform_igw': forms.Select(attrs={'class': 'form-select'}),
            'link_label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter link label'}),
            'cause': forms.Select(attrs={'class': 'form-select'}),
            'origin': forms.Select(attrs={'class': 'form-select'}),
            'impact_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the impact and any additional comments...'}),
        }
    
    def clean_link_label(self):
        """Validate link label format"""
        link_label = self.cleaned_data.get('link_label')
        if link_label:
            link_label = link_label.strip()
            if len(link_label) < 3:
                raise forms.ValidationError("Link label must be at least 3 characters long")
            if len(link_label) > 100:
                raise forms.ValidationError("Link label cannot exceed 100 characters")
        return link_label


def get_incident_form_class(network_type):
    """Helper function to get the appropriate form class for each network type"""
    form_classes = {
        'transport': TransportNetworkIncidentForm,
        'file_access': FileAccessNetworkIncidentForm,
        'radio_access': RadioAccessNetworkIncidentForm,
        'core': CoreNetworkIncidentForm,
        'backbone_internet': BackboneInternetNetworkIncidentForm,  # Fixed naming
    }
    return form_classes.get(network_type)

def update_form_common_fields(form, network_type):
    """Update form fields with dropdown choices from DropdownConfiguration"""
    try:
        # Import here to avoid circular imports
        from .models import DropdownConfiguration
        
        # Debug: Check if we have data
        total_configs = DropdownConfiguration.objects.count()
        print(f"DEBUG: Total dropdown configurations: {total_configs}")
        
        # Update cause choices
        if 'cause' in form.fields:
            cause_choices = [('', '--- Select Cause ---')]
            cause_configs = DropdownConfiguration.objects.filter(
                category='cause', 
                is_active=True
            ).order_by('sort_order', 'value')
            
            for config in cause_configs:
                cause_choices.append((config.value, config.value))
            
            form.fields['cause'].choices = cause_choices
            print(f"DEBUG: Cause choices set: {len(cause_choices)} options")
        
        # Update origin choices  
        if 'origin' in form.fields:
            origin_choices = [('', '--- Select Origin ---')]
            origin_configs = DropdownConfiguration.objects.filter(
                category='origin', 
                is_active=True
            ).order_by('sort_order', 'value')
            
            for config in origin_configs:
                origin_choices.append((config.value, config.value))
            
            form.fields['origin'].choices = origin_choices
            print(f"DEBUG: Origin choices set: {len(origin_choices)} options")
        
        # Network-specific dropdown updates
        if network_type == 'transport':
            if 'region_loop' in form.fields:
                region_choices = [('', '--- Select Region/Loop ---')]
                region_configs = DropdownConfiguration.objects.filter(
                    category='region_loop', 
                    is_active=True
                ).order_by('sort_order', 'value')
                
                for config in region_configs:
                    region_choices.append((config.value, config.value))
                
                form.fields['region_loop'].choices = region_choices
                print(f"DEBUG: Region choices set: {len(region_choices)} options")
            
            if 'system_capacity' in form.fields:
                system_choices = [('', '--- Select System/Capacity ---')]
                system_configs = DropdownConfiguration.objects.filter(
                    category='system_capacity', 
                    is_active=True
                ).order_by('sort_order', 'value')
                
                for config in system_configs:
                    system_choices.append((config.value, config.value))
                
                form.fields['system_capacity'].choices = system_choices
                print(f"DEBUG: System choices set: {len(system_choices)} options")
            
            # DOT extremity choices
            if 'dot_extremity_a' in form.fields:
                dot_choices = [('', '--- Select DOT State ---')]
                dot_configs = DropdownConfiguration.objects.filter(
                    category='dot_states', 
                    is_active=True
                ).order_by('sort_order', 'value')
                
                for config in dot_configs:
                    dot_choices.append((config.value, config.value))
                
                form.fields['dot_extremity_a'].choices = dot_choices
                form.fields['dot_extremity_b'].choices = dot_choices
                print(f"DEBUG: DOT choices set: {len(dot_choices)} options")
    
    except Exception as e:
        print(f"ERROR in update_form_common_fields: {e}")
        import traceback
        traceback.print_exc()
    
    return form

def populate_sample_dropdown_data():
    """Populate sample dropdown configuration data if not exists"""
    sample_data = [
        # Causes
        ('cause', 'Power Failure', 1),
        ('cause', 'Fiber Cut', 2),
        ('cause', 'Equipment Failure', 3),
        ('cause', 'Software Bug', 4),
        ('cause', 'Human Error', 5),
        ('cause', 'Natural Disaster', 6),
        ('cause', 'Network Congestion', 7),
        ('cause', 'Other', 99),
        
        # Origins
        ('origin', 'Internal System', 1),
        ('origin', 'External Provider', 2),
        ('origin', 'Customer Site', 3),
        ('origin', 'Data Center', 4),
        ('origin', 'Field Equipment', 5),
        ('origin', 'Third Party', 6),
        ('origin', 'Unknown', 7),
        ('origin', 'Other', 99),
        
        # Transport Network
        ('region_loop', 'North Region', 1),
        ('region_loop', 'South Region', 2),
        ('region_loop', 'East Region', 3),
        ('region_loop', 'West Region', 4),
        ('region_loop', 'Central Loop', 5),
        
        ('system_capacity', 'STM-1', 1),
        ('system_capacity', 'STM-4', 2),
        ('system_capacity', 'STM-16', 3),
        ('system_capacity', 'STM-64', 4),
        ('system_capacity', '10GE', 5),
        
        ('dot_states', 'Adrar', 1),
        ('dot_states', 'Chlef', 2),
        ('dot_states', 'Laghouat', 3),
        ('dot_states', 'Oum El Bouaghi', 4),
        ('dot_states', 'Batna', 5),
        
        # Wilayas for File Access and Radio Access
        ('wilayas', 'Adrar', 1),
        ('wilayas', 'Chlef', 2),
        ('wilayas', 'Laghouat', 3),
        ('wilayas', 'Oum El Bouaghi', 4),
        ('wilayas', 'Batna', 5),
        ('wilayas', 'Béjaïa', 6),
        ('wilayas', 'Biskra', 7),
        ('wilayas', 'Béchar', 8),
        ('wilayas', 'Blida', 9),
        ('wilayas', 'Bouira', 10),
        
        # Core Networks
        ('platforms', 'Core Platform 1', 1),
        ('platforms', 'Core Platform 2', 2),
        ('platforms', 'Metro Platform', 3),
        ('platforms', 'Access Platform', 4),
        
        ('region_nodes', 'Node-ALG-01', 1),
        ('region_nodes', 'Node-ORA-01', 2),
        ('region_nodes', 'Node-CST-01', 3),
        ('region_nodes', 'Node-ANN-01', 4),
        
        # Backbone Internet
        ('interconnect_types', 'BGP Peering', 1),
        ('interconnect_types', 'Transit Link', 2),
        ('interconnect_types', 'IXP Connection', 3),
        ('interconnect_types', 'Satellite Link', 4),
        
        ('platform_igws', 'IGW-ALG-01', 1),
        ('platform_igws', 'IGW-ORA-01', 2),
        ('platform_igws', 'IGW-CST-01', 3),
        ('platform_igws', 'Platform-INT-01', 4),
    ]
    
    for category, value, sort_order in sample_data:
        DropdownConfiguration.objects.get_or_create(
            category=category,
            value=value,
            defaults={
                'is_active': True,
                'sort_order': sort_order
            }
        )

# ===== SEARCH FORMS FOR TASK 2.4 =====

class BaseSearchForm(forms.Form):
    """Base search form with common search fields for all networks"""
    
    # Text search field
    search_query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search incidents by ID, location, comment...',
            'id': 'search-input'
        })
    )
    
    # Date range filters
    date_from = forms.DateTimeField(
        required=False,
        label='From Date',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
            'id': 'date-from'
        })
    )
    
    date_to = forms.DateTimeField(
        required=False,
        label='To Date', 
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local',
            'id': 'date-to'
        })
    )
    
    # Status filter
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('active', 'Active Incidents'),
        ('resolved', 'Resolved Incidents'),
        ('new', 'New (< 1 hour)'),
        ('low', 'Low Severity (1-2 hours)'),
        ('medium', 'Medium Severity (2-4 hours)'),
        ('critical', 'Critical (> 4 hours)'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'status-filter'
        })
    )
    
    # Cause filter (will be populated dynamically)
    cause = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'cause-filter'
        })
    )
    
    # Origin filter (will be populated dynamically)
    origin = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'origin-filter'
        })
    )
    
    # Sort options
    SORT_CHOICES = [
        ('-date_time_incident', 'Newest First'),
        ('date_time_incident', 'Oldest First'),
        ('-date_time_recovery', 'Recently Resolved'),
        ('date_time_recovery', 'Longest Resolved'),
        ('created_by__username', 'Created By'),
    ]
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-date_time_incident',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'sort-select'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._populate_base_choices()
    
    def _populate_base_choices(self):
        """Populate cause and origin choices using your existing system"""
        try:
            # Populate cause choices using your existing system
            cause_choices = [('', 'All Causes')]
            cause_configs = DropdownConfiguration.objects.filter(
                category='cause', is_active=True
            ).order_by('sort_order', 'value')
            cause_choices.extend([(c.value, c.value) for c in cause_configs])
            self.fields['cause'].choices = cause_choices
            
            # Populate origin choices using your existing system
            origin_choices = [('', 'All Origins')]
            origin_configs = DropdownConfiguration.objects.filter(
                category='origin', is_active=True
            ).order_by('sort_order', 'value')
            origin_choices.extend([(o.value, o.value) for o in origin_configs])
            self.fields['origin'].choices = origin_choices
            
        except Exception as e:
            # Fallback if database not available
            self.fields['cause'].choices = [('', 'All Causes')]
            self.fields['origin'].choices = [('', 'All Origins')]

class TransportNetworkSearchForm(BaseSearchForm):
    """Search form specific to Transport Networks"""
    
    region_loop = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'region-filter'
        })
    )
    
    system_capacity = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select', 
            'id': 'system-filter'
        })
    )
    
    extremity_a = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search Extremity A...'
        })
    )
    
    extremity_b = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search Extremity B...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._populate_transport_choices()
    
    def _populate_transport_choices(self):
        """Populate transport-specific choices using your existing system"""
        try:
            # Region/Loop choices
            region_choices = [('', 'All Regions')]
            region_configs = DropdownConfiguration.objects.filter(
                category='region_loop', is_active=True
            ).order_by('sort_order', 'value')
            region_choices.extend([(c.value, c.value) for c in region_configs])
            self.fields['region_loop'].choices = region_choices
            
            # System/Capacity choices
            system_choices = [('', 'All Systems')]
            system_configs = DropdownConfiguration.objects.filter(
                category='system_capacity', is_active=True
            ).order_by('sort_order', 'value')
            system_choices.extend([(c.value, c.value) for c in system_configs])
            self.fields['system_capacity'].choices = system_choices
            
        except Exception as e:
            # Fallback if database not available
            self.fields['region_loop'].choices = [('', 'All Regions')]
            self.fields['system_capacity'].choices = [('', 'All Systems')]

class FileAccessNetworkSearchForm(BaseSearchForm):
    """Search form specific to File Access Networks"""
    
    do_wilaya = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'wilaya-filter'
        })
    )
    
    zone_metro = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search Zone/Metro...'
        })
    )
    
    site = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search Site...'
        })
    )
    
    ip_address = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search IP Address...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._populate_file_access_choices()
    
    def _populate_file_access_choices(self):
        """Populate file access specific choices"""
        try:
            # Wilaya choices using your existing category name
            wilaya_choices = [('', 'All Wilayas')]
            wilaya_configs = DropdownConfiguration.objects.filter(
                category='wilayas', is_active=True
            ).order_by('sort_order', 'value')
            wilaya_choices.extend([(c.value, c.value) for c in wilaya_configs])
            self.fields['do_wilaya'].choices = wilaya_choices
            
        except Exception as e:
            self.fields['do_wilaya'].choices = [('', 'All Wilayas')]

class RadioAccessNetworkSearchForm(BaseSearchForm):
    """Search form specific to Radio Access Networks"""
    
    do_wilaya = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'wilaya-filter'
        })
    )
    
    site = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search Site...'
        })
    )
    
    ip_address = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search IP Address...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._populate_radio_access_choices()
    
    def _populate_radio_access_choices(self):
        """Populate radio access specific choices"""
        try:
            # Wilaya choices
            wilaya_choices = [('', 'All Wilayas')]
            wilaya_configs = DropdownConfiguration.objects.filter(
                category='wilayas', is_active=True
            ).order_by('sort_order', 'value')
            wilaya_choices.extend([(c.value, c.value) for c in wilaya_configs])
            self.fields['do_wilaya'].choices = wilaya_choices
            
        except Exception as e:
            self.fields['do_wilaya'].choices = [('', 'All Wilayas')]

class CoreNetworkSearchForm(BaseSearchForm):
    """Search form specific to Core Networks"""
    
    platform = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'platform-filter'
        })
    )
    
    region_node = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'region-node-filter'
        })
    )
    
    site = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search Site...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._populate_core_choices()
    
    def _populate_core_choices(self):
        """Populate core network specific choices"""
        try:
            # Platform choices
            platform_choices = [('', 'All Platforms')]
            platform_configs = DropdownConfiguration.objects.filter(
                category='platforms', is_active=True
            ).order_by('sort_order', 'value')
            platform_choices.extend([(c.value, c.value) for c in platform_configs])
            self.fields['platform'].choices = platform_choices
            
            # Region/Node choices
            region_node_choices = [('', 'All Regions/Nodes')]
            region_node_configs = DropdownConfiguration.objects.filter(
                category='region_nodes', is_active=True
            ).order_by('sort_order', 'value')
            region_node_choices.extend([(c.value, c.value) for c in region_node_configs])
            self.fields['region_node'].choices = region_node_choices
            
        except Exception as e:
            self.fields['platform'].choices = [('', 'All Platforms')]
            self.fields['region_node'].choices = [('', 'All Regions/Nodes')]

class BackboneInternetNetworkSearchForm(BaseSearchForm):
    """Search form specific to Backbone Internet Networks"""
    
    interconnect_type = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'interconnect-filter'
        })
    )
    
    platform_igw = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'platform-igw-filter'
        })
    )
    
    link_label = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search Link Label...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._populate_backbone_choices()
    
    def _populate_backbone_choices(self):
        """Populate backbone internet specific choices"""
        try:
            # Interconnect type choices
            interconnect_choices = [('', 'All Types')]
            interconnect_configs = DropdownConfiguration.objects.filter(
                category='interconnect_types', is_active=True
            ).order_by('sort_order', 'value')
            interconnect_choices.extend([(c.value, c.value) for c in interconnect_configs])
            self.fields['interconnect_type'].choices = interconnect_choices
            
            # Platform IGW choices
            platform_igw_choices = [('', 'All Platforms/IGWs')]
            platform_igw_configs = DropdownConfiguration.objects.filter(
                category='platform_igws', is_active=True
            ).order_by('sort_order', 'value')
            platform_igw_choices.extend([(c.value, c.value) for c in platform_igw_configs])
            self.fields['platform_igw'].choices = platform_igw_choices
            
        except Exception as e:
            self.fields['interconnect_type'].choices = [('', 'All Types')]
            self.fields['platform_igw'].choices = [('', 'All Platforms/IGWs')]

# Helper function for search forms
def get_search_form_class(network_type):
    """Helper function to get the appropriate search form class for each network type"""
    search_form_classes = {
        'transport': TransportNetworkSearchForm,
        'file_access': FileAccessNetworkSearchForm,
        'radio_access': RadioAccessNetworkSearchForm,
        'core': CoreNetworkSearchForm,
        'backbone_internet': BackboneInternetNetworkSearchForm,
    }
    return search_form_classes.get(network_type)