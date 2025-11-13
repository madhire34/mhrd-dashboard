from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter

from . import views
from .api import StateViewSet, SchemeViewSet, InitiativeViewSet

app_name = 'dashboard'

router = DefaultRouter()
router.register(r'states', StateViewSet, basename='db-states')
router.register(r'schemes', SchemeViewSet, basename='db-schemes')
router.register(r'initiatives', InitiativeViewSet, basename='db-initiatives')

urlpatterns = [

    path('', views.overview, name='overview'),
    path('dashboard', views.overview, name='dashboard'),
    path('states', views.states_list, name='states-list'),
    path('states/<slug:state_slug>', views.state_detail, name='state-detail'),
    path('states/<slug:state_slug>/print', views.state_print, name='state-print'),
    path('states/<slug:state_slug>/pdf', views.state_pdf, name='state-pdf'),
    path('schemes', views.schemes_list, name='schemes-list'),
    path('schemes/<slug:scheme_slug>', views.scheme_detail, name='scheme-detail'),
    path('schemes/<slug:scheme_slug>/print', views.scheme_print, name='scheme-print'),
    path('schemes/<slug:scheme_slug>/pdf', views.scheme_pdf, name='scheme-pdf'),
    path('compare', views.compare_view, name='compare'),
    path('reports', views.reports_list, name='reports-list'),
    path('reports/<slug:report_id>', views.report_detail, name='report-detail'),

    
    path('api/data/', views.dashboard_data, name='dashboard-data'),
    path('api/map/', views.state_map_data, name='state-map-data'),
    path('reports/download/', views.download_report, name='download-report'),

  
    path('api/v1/health', views.api_health, name='api-health'),
    path('api/v1/meta', views.api_meta, name='api-meta'),
    path('api/v1/kpis', views.api_kpis, name='api-kpis'),
    path('api/v1/trends', views.api_trends, name='api-trends'),
    path('api/v1/map', views.api_map, name='api-map'),
    path('api/v1/schemes', views.api_schemes, name='api-schemes'),
    path('api/v1/schemes/<slug:scheme_id>/kpis', views.api_scheme_kpis, name='api-scheme-kpis'),
    path('api/v1/reports', views.api_create_report, name='api-create-report'),  # POST
    path('api/v1/reports/<slug:report_id>', views.api_get_report, name='api-get-report'),
    path('api/v1/exports/data.csv', views.api_export_csv, name='api-export-csv'),
    path('api/v1/search', views.api_search, name='api-search'),
    path('api/v1/compare/trends', views.api_compare_trends, name='api-compare-trends'),
    path('api/v1/db/', include(router.urls)),
]
