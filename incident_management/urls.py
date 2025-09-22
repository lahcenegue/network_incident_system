from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Built-in Django admin
    path('admin/', admin.site.urls),
    
    # Authentication system
    path('auth/', include('authentication.urls')),
    
    # Main dashboard (homepage)
    path('', include('dashboard.urls')),
    
    # Incidents management
    path('incidents/', include('incidents.urls')),
    
    # Notifications system  
    path('notifications/', include('notifications.urls')),
    
    # Custom admin panel (separate from Django admin)
    path('admin-panel/', include('admin_panel.urls')),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)