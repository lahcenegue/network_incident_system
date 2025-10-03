"""
Celery tasks for incident management
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from .models import (
    TransportNetworkIncident,
    FileAccessNetworkIncident,
    RadioAccessNetworkIncident,
    CoreNetworkIncident,
    BackboneInternetNetworkIncident,
)


@shared_task(bind=True, name='incidents.tasks.auto_archive_eligible_incidents')
def auto_archive_eligible_incidents(self):
    """
    Automatically archive all eligible incidents across all network types.
    
    This task runs periodically (configured in Celery beat schedule)
    and archives incidents that meet all archival criteria:
    1. Resolved (has date_time_recovery)
    2. Has cause filled
    3. Has origin filled
    4. 2+ hours passed since resolution
    5. Not already archived
    
    Returns:
        dict: Summary of archival results
    """
    from authentication.models import CustomUser
    
    # Get system user for automatic archival (create if doesn't exist)
    system_user, created = CustomUser.objects.get_or_create(
        username='system_archival',
        defaults={
            'email': 'system@incident-management.local',
            'role': 'admin',
            'is_active': True,
            'is_staff': True,
        }
    )
    
    if created:
        system_user.set_unusable_password()
        system_user.save()
    
    # Track results
    results = {
        'total_checked': 0,
        'total_archived': 0,
        'by_network_type': {},
        'errors': [],
        'timestamp': timezone.now().isoformat(),
    }
    
    # All network models to check
    network_models = {
        'transport': TransportNetworkIncident,
        'file_access': FileAccessNetworkIncident,
        'radio_access': RadioAccessNetworkIncident,
        'core': CoreNetworkIncident,
        'backbone_internet': BackboneInternetNetworkIncident,
    }
    
    # Process each network type
    for network_name, model_class in network_models.items():
        network_archived = 0
        network_checked = 0
        network_errors = []
        
        try:
            # Get all resolved, non-archived incidents with cause and origin
            eligible_incidents = model_class.objects.filter(
                is_resolved=True,
                is_archived=False,
                date_time_recovery__isnull=False,
            ).exclude(
                Q(cause__isnull=True) | Q(cause='') |
                Q(origin__isnull=True) | Q(origin='')
            )
            
            network_checked = eligible_incidents.count()
            results['total_checked'] += network_checked
            
            # Check each incident for archival eligibility
            for incident in eligible_incidents:
                try:
                    if incident.can_be_archived():
                        success = incident.archive(system_user)
                        if success:
                            network_archived += 1
                            results['total_archived'] += 1
                        else:
                            network_errors.append(
                                f"Failed to archive {incident.id}"
                            )
                except Exception as e:
                    error_msg = f"Error archiving {incident.id}: {str(e)}"
                    network_errors.append(error_msg)
                    results['errors'].append(error_msg)
            
            # Store network-specific results
            results['by_network_type'][network_name] = {
                'checked': network_checked,
                'archived': network_archived,
                'errors': network_errors,
            }
            
        except Exception as e:
            error_msg = f"Error processing {network_name}: {str(e)}"
            results['errors'].append(error_msg)
            results['by_network_type'][network_name] = {
                'checked': 0,
                'archived': 0,
                'errors': [error_msg],
            }
    
    # Log results
    print(f"Auto-archival completed: {results['total_archived']} incidents archived out of {results['total_checked']} checked")
    
    return results


@shared_task(bind=True, name='incidents.tasks.test_celery')
def test_celery(self):
    """
    Simple test task to verify Celery is working
    """
    print("Celery test task executed successfully!")
    return {
        'status': 'success',
        'message': 'Celery is working correctly',
        'timestamp': timezone.now().isoformat(),
    }