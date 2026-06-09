
from django.urls import path
from . import views, api

# Es buena práctica ponerle un nombre a tu app para referenciar las URLs más fácil después
app_name = 'core'

urlpatterns = [
    # path('ruta-en-el-navegador/', funcion_de_la_vista, nombre_para_referenciar),
    path('', views.home, name='home'),             # Será http://127.0.0.1:8000/
    path("registro/", views.registro, name="registro"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path('mapa/', views.map_view, name='map'),      # Será http://127.0.0.1:8000/mapa/
    path('admin-panel/', views.admin_view, name='admin_panel'),
    path('campus/', views.campus_view, name='campus'),
    path('campus/invitado/', views.campus_guest_view, name='campus_guest'),
    path('qr/', views.qr_view, name='qr'),
    path('ruta/', views.route_view, name='route'),
    path('detalle/', views.detail_view, name='detail'),
    
    # API Admin endpoints
    path('api/admin/usuarios/stats/', api.api_usuarios_stats, name='api_usuarios_stats'),
    path('api/admin/usuarios/', api.api_usuarios_listar, name='api_usuarios_listar'),
    path('api/favoritos/', api.api_favoritos_list, name='api_favoritos_list'),
    path('api/favoritos/guardar/', api.api_favoritos_guardar, name='api_favoritos_guardar'),
    path('api/historial/', api.api_historial_list, name='api_historial_list'),
    path('api/historial/registrar/', api.api_historial_registrar, name='api_historial_registrar'),
]