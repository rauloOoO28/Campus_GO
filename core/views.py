from django.shortcuts import render
from locations.models import Campus, Ubicacion
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import RegistroForm
from django.contrib import messages

def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # opcional: inicia sesión tras registrar
            messages.success(request, "Registro exitoso.")
            return redirect("core:campus")
        else:
            for field_errors in form.errors.values():
                for error in field_errors:
                    messages.error(request, error)
    else:
        form = RegistroForm()
    return render(request, "core/registro.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect("core:campus")
        else:
            messages.error(request, "Correo o contraseña inválida.")
    return render(request, "core/login.html")

# Vista principal (Inicio)
def home(request):
    # NOTA: Django ya busca dentro de 'templates', así que solo ponemos 'core/archivo.html'
    return render(request, 'core/index.html')


# Vista del Mapa
def map_view(request):
    perfil = None
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
        except:
            perfil = None
    return render(request, 'core/map.html', {'perfil': perfil})

# Vista de Administrador
def admin_view(request):
    perfil = None
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
        except:
            perfil = None
    return render(request, 'core/admin.html', {'perfil': perfil})

# Vista de Campus
def campus_view(request):
    """
    Vista de selección de campus.
    ESCOM se carga real desde la BD; los otros 3 son demos visuales.
    """
    # Obtener perfil del usuario si está autenticado
    perfil = None
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
        except:
            perfil = None
    
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
        'perfil': perfil,
    })

def qr_view(request):
    perfil = None
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
        except:
            perfil = None
    return render(request, 'core/qr.html', {'perfil': perfil})

def route_view(request):
    perfil = None
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
        except:
            perfil = None
    return render(request, 'core/route.html', {'perfil': perfil})

def detail_view(request):
    perfil = None
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil
        except:
            perfil = None
    return render(request, 'core/detail.html', {'perfil': perfil})


# Puedes seguir agregando def qr_view, def route_view, etc. siguiendo la misma lógica...
