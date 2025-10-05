from django.urls import path
from . import views

app_name = 'incidents'

urlpatterns = [
    # Transport Networks
    path('transport-networks/', views.network_incidents_view, {'network_type': 'transport'}, name='transport_incidents'),
    path('transport-networks/add/', views.add_incident_view, {'network_type': 'transport'}, name='add_transport_incident'),
    path('transport-networks/edit/<uuid:incident_id>/', views.edit_incident_view, {'network_type': 'transport'}, name='edit_transport_incident'),
    path('transport-networks/historical/', views.historical_incidents_view, {'network_type': 'transport'}, name='transport_historical'),
    path('transport-networks/notification/<uuid:incident_id>/', views.incident_notification_prompt, {'network_type': 'transport'}, name='transport_incidents_with_notification'),
    
    # File Access Networks
    path('file-access-networks/', views.network_incidents_view, {'network_type': 'file_access'}, name='file_access_incidents'),
    path('file-access-networks/add/', views.add_incident_view, {'network_type': 'file_access'}, name='add_file_access_incident'),
    path('file-access-networks/edit/<uuid:incident_id>/', views.edit_incident_view, {'network_type': 'file_access'}, name='edit_file_access_incident'),
    path('file-access-networks/historical/', views.historical_incidents_view, {'network_type': 'file_access'}, name='file_access_historical'),
    path('file-access-networks/notification/<uuid:incident_id>/', views.incident_notification_prompt, {'network_type': 'file_access'}, name='file_access_incidents_with_notification'),
    
    # Radio Access Networks
    path('radio-access-networks/', views.network_incidents_view, {'network_type': 'radio_access'}, name='radio_access_incidents'),
    path('radio-access-networks/add/', views.add_incident_view, {'network_type': 'radio_access'}, name='add_radio_access_incident'),
    path('radio-access-networks/edit/<uuid:incident_id>/', views.edit_incident_view, {'network_type': 'radio_access'}, name='edit_radio_access_incident'),
    path('radio-access-networks/historical/', views.historical_incidents_view, {'network_type': 'radio_access'}, name='radio_access_historical'),
    path('radio-access-networks/notification/<uuid:incident_id>/', views.incident_notification_prompt, {'network_type': 'radio_access'}, name='radio_access_incidents_with_notification'),
    
    # Core Networks
    path('core-networks/', views.network_incidents_view, {'network_type': 'core'}, name='core_incidents'),
    path('core-networks/add/', views.add_incident_view, {'network_type': 'core'}, name='add_core_incident'),
    path('core-networks/edit/<uuid:incident_id>/', views.edit_incident_view, {'network_type': 'core'}, name='edit_core_incident'),
    path('core-networks/historical/', views.historical_incidents_view, {'network_type': 'core'}, name='core_historical'),
    path('core-networks/notification/<uuid:incident_id>/', views.incident_notification_prompt, {'network_type': 'core'}, name='core_incidents_with_notification'),
    
    # Backbone Internet Networks
    path('backbone-internet-networks/', views.network_incidents_view, {'network_type': 'backbone_internet'}, name='backbone_internet_incidents'),
    path('backbone-internet-networks/add/', views.add_incident_view, {'network_type': 'backbone_internet'}, name='add_backbone_internet_incident'),
    path('backbone-internet-networks/edit/<uuid:incident_id>/', views.edit_incident_view, {'network_type': 'backbone_internet'}, name='edit_backbone_internet_incident'),
    path('backbone-internet-networks/historical/', views.historical_incidents_view, {'network_type': 'backbone_internet'}, name='backbone_internet_historical'),
    path('backbone-internet-networks/notification/<uuid:incident_id>/', views.incident_notification_prompt, {'network_type': 'backbone_internet'}, name='backbone_internet_incidents_with_notification'),
    
    # Unified Historical View (All Networks)
    path('historical/', views.unified_historical_incidents_view, name='unified_historical'),
    path('historical/restore/<uuid:incident_id>/<str:network_type>/', views.restore_archived_incident, name='restore_incident'),
    path('archive/<uuid:incident_id>/<str:network_type>/', views.archive_incident_manual, name='archive_incident_manual'),
    path('bulk-archive/', views.bulk_archive_incidents, name='bulk_archive_incidents'),
    
    # AJAX endpoints for validation
    path('validate-field/<str:network_type>/', views.validate_incident_field, name='validate_field'),
    path('ajax-search/<str:network_type>/', views.ajax_search_incidents, name='ajax_search'),

    # Incident detail modal endpoint
    path('<str:network_type>/detail/<uuid:incident_id>/', views.get_incident_detail, name='incident_detail'),

    # Saved Search endpoints (Task 1: Phase 4)
    path('saved-search/<str:network_type>/save/', views.save_search_view, name='save_search'),
    path('saved-search/<str:network_type>/list/', views.list_saved_searches_view, name='list_saved_searches'),
    path('saved-search/<uuid:search_id>/load/', views.load_saved_search_view, name='load_saved_search'),
    path('saved-search/<uuid:search_id>/delete/', views.delete_saved_search_view, name='delete_saved_search'),
    path('saved-search/<uuid:search_id>/set-default/', views.set_default_search_view, name='set_default_search'),

    # CSV/Excel Export endpoints (Task 2: Phase 4)
    path('export/<str:network_type>/', views.export_incidents_view, name='export_incidents'),
    path('export-all-networks/', views.bulk_export_all_networks, name='export_all_networks'),
]