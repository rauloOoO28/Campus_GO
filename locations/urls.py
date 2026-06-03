"""
locations/urls.py

CORRECCIÓN: el prefijo cambió de /admin/grafo/ a /grafo/ para no colisionar
con Django Admin (que captura todo lo que empieza con admin/).

El editor sigue protegido con @staff_member_required en las vistas,
así que solo los administradores pueden acceder.
"""

from django.urls import path
from . import views, views_editor, api

 
app_name = 'locations'

urlpatterns = [
    # QRs públicos
    path('qr/<slug:codigo>/', views.resolver_qr, name='resolver_qr'),
    path('ubicacion/<slug:codigo>/', views.detalle_publico, name='detalle_publico'),

    # API pública del mapa
    path('api/campus/<slug:codigo_campus>/ubicaciones/',
         views.api_ubicaciones_campus,
         name='api_ubicaciones_campus'),
    path('api/ruta/', views.api_calcular_ruta, name='api_calcular_ruta'),

    # ============================================================
    # ⭐ Editor visual del grafo (requiere ser staff)
    # ============================================================
    path('grafo/<slug:codigo_campus>/',
         views_editor.editor_grafo_view,
         name='admin_editor_grafo'),

    # API del editor (AJAX)
    path('grafo/<slug:codigo_campus>/api/data/',
         views_editor.api_editor_data,
         name='admin_editor_data'),
    path('grafo/<slug:codigo_campus>/api/nodo/crear/',
         views_editor.api_crear_nodo,
         name='admin_editor_crear_nodo'),
    path('grafo/<slug:codigo_campus>/api/nodo/<int:nodo_id>/actualizar/',
         views_editor.api_actualizar_nodo,
         name='admin_editor_actualizar_nodo'),
    path('grafo/<slug:codigo_campus>/api/nodo/<int:nodo_id>/eliminar/',
         views_editor.api_eliminar_nodo,
         name='admin_editor_eliminar_nodo'),
    path('grafo/<slug:codigo_campus>/api/arista/crear/',
         views_editor.api_crear_arista,
         name='admin_editor_crear_arista'),
    path('grafo/<slug:codigo_campus>/api/arista/<int:arista_id>/eliminar/',
         views_editor.api_eliminar_arista,
         name='admin_editor_eliminar_arista'),
      # API Admin endpoints
    path('api/admin/stats/', api.api_stats, name='api_stats'),
    path('api/admin/ubicaciones/', api.api_ubicaciones, name='api_ubicaciones'),
    path('api/admin/edificios/', api.api_edificios, name='api_edificios'),
    path('api/admin/campus/', api.api_campus, name='api_campus'),
    path('api/admin/ubicaciones/crear/', api.api_ubicaciones_crear, name='api_ubicaciones_crear'),
    path('api/admin/ubicaciones/<int:ubicacion_id>/editar/', api.api_ubicaciones_editar, name='api_ubicaciones_editar'),
    path('api/admin/ubicaciones/<int:ubicacion_id>/eliminar/', api.api_ubicaciones_eliminar, name='api_ubicaciones_eliminar'),
]
    
   
