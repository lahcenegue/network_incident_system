from django.urls import path
from . import views

app_name = 'incidents'

urlpatterns = [
    # Transport Networks
    path('transport/', views.TransportListView.as_view(), name='transport_list'),
    path('transport/create/', views.TransportCreateView.as_view(), name='transport_create'),
    path('transport/historical/', views.TransportHistoricalView.as_view(), name='transport_historical'),
    
    # File Access Networks
    path('file-access/', views.FileAccessListView.as_view(), name='file_access_list'),
    path('file-access/create/', views.FileAccessCreateView.as_view(), name='file_access_create'),
    path('file-access/historical/', views.FileAccessHistoricalView.as_view(), name='file_access_historical'),
    
    # Radio Access Networks
    path('radio-access/', views.RadioAccessListView.as_view(), name='radio_access_list'),
    path('radio-access/create/', views.RadioAccessCreateView.as_view(), name='radio_access_create'),
    path('radio-access/historical/', views.RadioAccessHistoricalView.as_view(), name='radio_access_historical'),
    
    # Core Networks
    path('core/', views.CoreListView.as_view(), name='core_list'),
    path('core/create/', views.CoreCreateView.as_view(), name='core_create'),
    path('core/historical/', views.CoreHistoricalView.as_view(), name='core_historical'),
    
    # Backbone Internet Networks
    path('backbone/', views.BackboneListView.as_view(), name='backbone_list'),
    path('backbone/create/', views.BackboneCreateView.as_view(), name='backbone_create'),
    path('backbone/historical/', views.BackboneHistoricalView.as_view(), name='backbone_historical'),
]