from django.shortcuts import render
from locations.models import Campus, Ubicacion

# Vista principal (Inicio)
def home(request):
    # NOTA: Django ya busca dentro de 'templates', así que solo ponemos 'core/archivo.html'
    return render(request, 'core/index.html')

# Vista de Login
def login_view(request):
    return render(request, 'core/login.html')

# Vista del Mapa
def map_view(request):
    return render(request, 'core/map.html')

# Vista de Administrador
def admin_view(request):
    return render(request, 'core/admin.html')

# Vista de Campus
def campus_view(request):
    """
    Vista de selección de campus.
    ESCOM se carga real desde la BD; los otros 3 son demos visuales.
    """
    # Intentar cargar ESCOM desde la BD
    try:
        escom = Campus.objects.get(codigo='escom-ipn', activo=True)
        escom_data = {
            'existe': True,
            'nombre':           escom.nombre,
            'direccion':        escom.direccion,
            'total_edificios':  escom.edificios.count(),
            'total_ubicaciones': escom.ubicaciones.filter(activo=True).count(),
            'total_qrs':        sum(
                1 for u in escom.ubicaciones.filter(activo=True)
                if u.tiene_qr
            ),
        }
    except Campus.DoesNotExist:
        # Si todavía no se ha corrido el comando cargar_escom
        escom_data = {
            'existe': False,
            'nombre':            'ESCOM IPN',
            'direccion':         'Av. Juan de Dios Bátiz, Lindavista',
            'total_edificios':   0,
            'total_ubicaciones': 0,
            'total_qrs':         0,
        }
 
    return render(request, 'core/campus.html', {
        'escom': escom_data,
    })

def qr_view(request):
    return render(request, 'core/qr.html')

def route_view(request):
    return render(request, 'core/route.html')

def detail_view(request):
    return render(request, 'core/detail.html')


# Puedes seguir agregando def qr_view, def route_view, etc. siguiendo la misma lógica...

# Vista de Registro
def register_view(request):
    return render(request, 'core/registro.html')