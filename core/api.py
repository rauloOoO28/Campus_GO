"""
core/api.py - API endpoints para estadísticas y gestión de usuarios
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from .models import Perfil


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
