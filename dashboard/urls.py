from django.urls import path
from . import views

app_name = 'dashboard' 

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/refresh-charts/', views.refresh_chart_data, name='refresh_charts'),
    path('generate-pdf/', views.generate_pdf_report, name='generate_pdf'),
]