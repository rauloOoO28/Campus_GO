"""
locations/urls.py
 
URLs públicas y API de la app locations.
"""
 
from django.urls import path
from . import views, api
 
app_name = 'locations'
 
urlpatterns = [
    # URL pública a la que apuntan los QRs
    path('qr/<slug:codigo>/', views.resolver_qr, name='resolver_qr'),
 
    # Misma página pero acceso desde navegación interna
    path('ubicacion/<slug:codigo>/', views.detalle_publico, name='detalle_publico'),
 
    # API JSON que alimenta el mapa
    path('api/campus/<slug:codigo_campus>/ubicaciones/',
         views.api_ubicaciones_campus,
         name='api_ubicaciones_campus'),
    
    # API Admin endpoints
    path('api/admin/stats/', api.api_stats, name='api_stats'),
    path('api/admin/ubicaciones/', api.api_ubicaciones, name='api_ubicaciones'),
    path('api/admin/edificios/', api.api_edificios, name='api_edificios'),
    path('api/admin/campus/', api.api_campus, name='api_campus'),
    path('api/admin/ubicaciones/crear/', api.api_ubicaciones_crear, name='api_ubicaciones_crear'),
    path('api/admin/ubicaciones/<int:ubicacion_id>/editar/', api.api_ubicaciones_editar, name='api_ubicaciones_editar'),
    path('api/admin/ubicaciones/<int:ubicacion_id>/eliminar/', api.api_ubicaciones_eliminar, name='api_ubicaciones_eliminar'),
]
 