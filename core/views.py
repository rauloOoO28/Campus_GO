from django.shortcuts import render
from locations.models import Campus, Ubicacion, Edificio, CodigoQR, NodoGrafo, AristaGrafo
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from .forms import RegistroForm
from django.contrib import messages


def es_admin_check(user):
    return user.is_superuser

class PerfilFallback:
    def __init__(self, nombre_completo, rol_display):
        self.nombre_completo = nombre_completo
        self._rol_display = rol_display

    def get_rol_display(self):
        return self._rol_display


def get_user_profile(request):
    if request.user.is_authenticated:
        try:
            return request.user.perfil
        except Exception:
            nombre = request.user.get_full_name() or request.user.email or request.user.username
            rol = "Administrador" if request.user.is_superuser else "Usuario"
            return PerfilFallback(nombre, rol)
    return None


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
        if user is None:
            try:
                existing_user = User.objects.get(email__iexact=email)
                user = authenticate(request, username=existing_user.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            return redirect("core:campus")
        else:
            messages.error(request, "Correo o contraseña inválida.")
    return render(request, "core/login.html")

def logout_view(request):
    logout(request)
    return redirect("core:login")

def campus_guest_view(request):
    logout(request)
    return redirect("core:campus")

# Vista principal (Inicio)
def home(request):
    # NOTA: Django ya busca dentro de 'templates', así que solo ponemos 'core/archivo.html'
    return render(request, 'core/index.html')


# Vista del Mapa
def map_view(request):
    perfil = get_user_profile(request)
    return render(request, 'core/map.html', {'perfil': perfil})

# Vista de Administrador
# Vista de Administrador
@user_passes_test(es_admin_check, login_url='/login/')
def admin_view(request):
    """
    Panel administrativo de CampusGo.
    Solo accesible para superusuarios (validación: es_admin_check).

    Carga conteos reales desde la BD para mostrar en las cards
    y tabs del panel personalizado.
    """
    perfil = get_user_profile(request)

    # ============================================================
    # CONTEOS REALES DESDE LA BD
    # ============================================================
    total_campus = Campus.objects.filter(activo=True).count()
    total_ubicaciones = Ubicacion.objects.filter(activo=True).count()
    total_edificios = Edificio.objects.count()
    total_qrs = CodigoQR.objects.count()
    total_usuarios = User.objects.count()
    total_nodos = NodoGrafo.objects.filter(activo=True).count()
    total_aristas = AristaGrafo.objects.filter(activo=True).count()
    total_escaneos = sum(qr.escaneos for qr in CodigoQR.objects.all())

    # Últimas 10 ubicaciones para la tabla
    ubicaciones_recientes = (
        Ubicacion.objects
        .select_related('campus', 'edificio')
        .prefetch_related('codigo_qr', 'nodo_grafo')
        .order_by('-creado')[:10]
    )

    # Campus activos para los cards del módulo Rutas
    campus_list = Campus.objects.filter(activo=True).order_by('nombre')

    return render(request, 'core/admin.html', {
        # Lo que tu compañero ya pasaba (intacto)
        'perfil': perfil,

        # Conteos nuevos
        'total_campus':       total_campus,
        'total_ubicaciones':  total_ubicaciones,
        'total_edificios':    total_edificios,
        'total_qrs':          total_qrs,
        'total_usuarios':     total_usuarios,
        'total_nodos':        total_nodos,
        'total_aristas':      total_aristas,
        'total_escaneos':     total_escaneos,

        # Datos para tabla y módulos
        'ubicaciones':        ubicaciones_recientes,
        'campus_list':        campus_list,
    })

# Vista de Campus
def campus_view(request):
    """
    Vista de selección de campus.
    ESCOM se carga real desde la BD; los otros 3 son demos visuales.
    """
    # Obtener perfil del usuario si está autenticado
    perfil = get_user_profile(request)
    
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
    perfil = get_user_profile(request)
    return render(request, 'core/qr.html', {'perfil': perfil})

def route_view(request):
    perfil = get_user_profile(request)
    return render(request, 'core/route.html', {'perfil': perfil})

def detail_view(request):
    perfil = get_user_profile(request)
    return render(request, 'core/detail.html', {'perfil': perfil})

