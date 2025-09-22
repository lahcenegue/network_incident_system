from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin (built-in)
    path('admin/', admin.site.urls),

    # Authentication URLs
    path('auth/', include('authentication.urls')),
    
    # Main application URLs
    path('', include('dashboard.urls')),  # Dashboard will be the home page
    path('incidents/', include('incidents.urls')),
    path('notifications/', include('notifications.urls')),
    
    # Separate admin panel (different URL structure as required)
    path('admin-panel/', include('admin_panel.urls')),
]