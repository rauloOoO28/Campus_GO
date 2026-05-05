from django.shortcuts import render

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
    return render(request, 'core/campus.html')

def qr_view(request):
    return render(request, 'core/qr.html')

def route_view(request):
    return render(request, 'core/route.html')

def detail_view(request):
    return render(request, 'core/detail.html')


# Puedes seguir agregando def qr_view, def route_view, etc. siguiendo la misma lógica...