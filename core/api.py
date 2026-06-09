"""
core/api.py - API endpoints para estadísticas y gestión de usuarios
"""

import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from locations.models import Campus
from .models import Perfil, Favorito, Historial


def es_admin(user):
    return user.is_superuser


@require_http_methods(["GET"])
@user_passes_test(es_admin, login_url='/login/')
def api_usuarios_stats(request):
    """Retorna estadísticas de usuarios"""
    try:
        total_users = User.objects.count()
        registered_perfiles = Perfil.objects.count()
        admin_users = User.objects.filter(is_superuser=True).count()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'usuarios_registrados': total_users,
                'perfiles_creados': registered_perfiles,
                'administradores': admin_users,
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def auth_json_required(view):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Necesitas iniciar sesión para acceder a esta acción.'}, status=403)
        return view(request, *args, **kwargs)
    return wrapper


@require_http_methods(["GET"])
@user_passes_test(es_admin, login_url='/login/')
def api_usuarios_listar(request):
    """Retorna lista de usuarios"""
    try:
        users = User.objects.all().prefetch_related('perfil')
        
        data = []
        for user in users:
            perfil_data = None
            try:
                perfil = user.perfil
                perfil_data = {
                    'nombre_completo': perfil.nombre_completo,
                    'rol': perfil.get_rol_display(),
                }
            except Perfil.DoesNotExist:
                pass
            
            data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
                'perfil': perfil_data,
                'date_joined': user.date_joined.isoformat(),
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(['GET'])
@auth_json_required
def api_favoritos_list(request):
    favoritos = Favorito.objects.filter(user=request.user).select_related('campus')
    return JsonResponse({
        'status': 'success',
        'data': [
            {
                'id': favorito.id,
                'codigo': favorito.campus.codigo,
                'nombre': favorito.campus.nombre,
                'direccion': favorito.campus.direccion,
                'guardado_el': favorito.creado.isoformat(),
            }
            for favorito in favoritos
        ]
    })


@require_http_methods(['POST'])
@auth_json_required
def api_favoritos_guardar(request):
    payload = {}
    if request.content_type and 'application/json' in request.content_type:
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            payload = {}
    codigo = payload.get('codigo') or payload.get('campus_codigo') or request.POST.get('codigo') or request.POST.get('campus_codigo')
    if not codigo:
        return JsonResponse({'status': 'error', 'message': 'Código de campus requerido.'}, status=400)

    campus = get_object_or_404(Campus, codigo=codigo, activo=True)
    favorito, created = Favorito.objects.get_or_create(user=request.user, campus=campus)
    return JsonResponse({
        'status': 'success',
        'data': {
            'created': created,
            'campus': {
                'codigo': campus.codigo,
                'nombre': campus.nombre,
                'direccion': campus.direccion,
            }
        }
    })


@require_http_methods(['GET'])
@auth_json_required
def api_historial_list(request):
    registros = Historial.objects.filter(user=request.user).select_related('campus')[:10]
    return JsonResponse({
        'status': 'success',
        'data': [
            {
                'id': registro.id,
                'codigo': registro.campus.codigo,
                'nombre': registro.campus.nombre,
                'direccion': registro.campus.direccion,
                'visitado_el': registro.visitado_el.isoformat(),
            }
            for registro in registros
        ]
    })


@require_http_methods(['POST'])
@auth_json_required
def api_historial_registrar(request):
    payload = {}
    if request.content_type and 'application/json' in request.content_type:
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}')
        except json.JSONDecodeError:
            payload = {}
    codigo = payload.get('codigo') or payload.get('campus_codigo') or request.POST.get('codigo') or request.POST.get('campus_codigo')
    if not codigo:
        return JsonResponse({'status': 'error', 'message': 'Código de campus requerido.'}, status=400)

    campus = get_object_or_404(Campus, codigo=codigo, activo=True)
    historial = Historial.objects.create(user=request.user, campus=campus)
    return JsonResponse({
        'status': 'success',
        'data': {
            'codigo': campus.codigo,
            'nombre': campus.nombre,
            'direccion': campus.direccion,
            'visitado_el': historial.visitado_el.isoformat(),
        }
    })
