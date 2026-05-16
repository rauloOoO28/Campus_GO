"""
locations/urls.py
 
URLs públicas y API de la app locations.
"""
 
from django.urls import path
from . import views
 
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
]
 