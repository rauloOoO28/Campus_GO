
from django.urls import path
from . import views

# Es buena práctica ponerle un nombre a tu app para referenciar las URLs más fácil después
app_name = 'core'

urlpatterns = [
    # path('ruta-en-el-navegador/', funcion_de_la_vista, nombre_para_referenciar),
    path('', views.home, name='home'),             # Será http://127.0.0.1:8000/
    path('login/', views.login_view, name='login'), # Será http://127.0.0.1:8000/login/
    path('mapa/', views.map_view, name='map'),      # Será http://127.0.0.1:8000/mapa/
    path('admin-panel/', views.admin_view, name='admin_panel'),
    path('campus/', views.campus_view, name='campus'),
    path('qr/', views.qr_view, name='qr'),
    path('ruta/', views.route_view, name='route'),
    path('detalle/', views.detail_view, name='detail'),
]