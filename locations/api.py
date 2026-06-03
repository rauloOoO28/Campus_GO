"""
locations/api.py - API endpoints para administración de campus, edificios y ubicaciones
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from .models import Campus, Edificio, Ubicacion
import json


def es_admin(user):
    return user.is_superuser


@require_http_methods(["GET"])
@user_passes_test(es_admin, login_url='/login/')
def api_stats(request):
    """Retorna estadísticas generales de la BD"""
    try:
        campus_count = Campus.objects.filter(activo=True).count()
        edificios_count = Edificio.objects.count()
        ubicaciones_count = Ubicacion.objects.filter(activo=True).count()
        qr_count = Ubicacion.objects.filter(activo=True, tiene_qr=True).count()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'campus_activos': campus_count,
                'edificios_totales': edificios_count,
                'ubicaciones_registradas': ubicaciones_count,
                'qr_generados': qr_count,
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["GET"])
@user_passes_test(es_admin, login_url='/login/')
def api_ubicaciones(request):
    """Retorna lista de ubicaciones con filtros opcionales"""
    try:
        campus_id = request.GET.get('campus_id')
        edificio_id = request.GET.get('edificio_id')
        tipo = request.GET.get('tipo')
        
        ubicaciones = Ubicacion.objects.filter(activo=True).select_related('campus', 'edificio')
        
        if campus_id:
            ubicaciones = ubicaciones.filter(campus_id=campus_id)
        if edificio_id:
            ubicaciones = ubicaciones.filter(edificio_id=edificio_id)
        if tipo:
            ubicaciones = ubicaciones.filter(tipo=tipo)
        
        data = []
        for ub in ubicaciones[:100]:  # Limitar a 100 para evitar sobrecarga
            data.append({
                'id': ub.id,
                'nombre': ub.nombre,
                'tipo': ub.get_tipo_display(),
                'tipo_slug': ub.tipo,
                'codigo': ub.codigo,
                'piso': ub.piso,
                'capacidad': ub.capacidad,
                'edificio': ub.edificio.nombre if ub.edificio else 'Exterior',
                'edificio_id': ub.edificio_id,
                'campus': ub.campus.nombre,
                'campus_id': ub.campus_id,
                'tiene_qr': ub.tiene_qr,
                'activo': ub.activo,
                'descripcion': ub.descripcion or '',
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["GET"])
@user_passes_test(es_admin, login_url='/login/')
def api_edificios(request):
    """Retorna lista de edificios"""
    try:
        campus_id = request.GET.get('campus_id')
        
        edificios = Edificio.objects.select_related('campus')
        if campus_id:
            edificios = edificios.filter(campus_id=campus_id)
        
        data = []
        for ed in edificios:
            data.append({
                'id': ed.id,
                'codigo': ed.codigo,
                'nombre': ed.nombre,
                'campus': ed.campus.nombre,
                'campus_id': ed.campus_id,
                'pisos': ed.pisos,
                'latitud': ed.latitud,
                'longitud': ed.longitud,
                'descripcion': ed.descripcion or '',
                'ubicaciones_count': ed.ubicaciones.count(),
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["GET"])
@user_passes_test(es_admin, login_url='/login/')
def api_campus(request):
    """Retorna lista de campus"""
    try:
        campus_list = Campus.objects.all()
        
        data = []
        for c in campus_list:
            data.append({
                'id': c.id,
                'codigo': c.codigo,
                'nombre': c.nombre,
                'direccion': c.direccion or '',
                'activo': c.activo,
                'descripcion': c.descripcion or '',
                'edificios_count': c.edificios.count(),
                'ubicaciones_count': c.ubicaciones.count(),
            })
        
        return JsonResponse({
            'status': 'success',
            'data': data,
            'total': len(data)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["POST"])
@user_passes_test(es_admin, login_url='/login/')
@csrf_exempt
def api_ubicaciones_crear(request):
    """Crea una nueva ubicación"""
    try:
        data = json.loads(request.body)
        
        # Validar campos requeridos
        required_fields = ['nombre', 'tipo', 'campus_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Campo requerido faltante: {field}'
                }, status=400)
        
        # Obtener campus
        campus = Campus.objects.get(id=data['campus_id'])
        
        # Obtener edificio si se proporciona
        edificio = None
        if data.get('edificio_id'):
            edificio = Edificio.objects.get(id=data['edificio_id'], campus=campus)
        
        # Crear ubicación
        ubicacion = Ubicacion.objects.create(
            campus=campus,
            edificio=edificio,
            tipo=data['tipo'],
            nombre=data['nombre'],
            codigo=data.get('codigo', ''),
            piso=data.get('piso', 0),
            capacidad=data.get('capacidad', 0),
            descripcion=data.get('descripcion', ''),
            activo=True,
            tiene_qr=data.get('tiene_qr', False),
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Ubicación creada exitosamente',
            'data': {
                'id': ubicacion.id,
                'nombre': ubicacion.nombre,
                'tipo': ubicacion.get_tipo_display(),
            }
        })
    except Campus.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Campus no encontrado'}, status=404)
    except Edificio.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Edificio no encontrado'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["POST"])
@user_passes_test(es_admin, login_url='/login/')
@csrf_exempt
def api_ubicaciones_editar(request, ubicacion_id):
    """Edita una ubicación existente"""
    try:
        ubicacion = Ubicacion.objects.get(id=ubicacion_id)
        data = json.loads(request.body)
        
        # Actualizar campos
        if 'nombre' in data:
            ubicacion.nombre = data['nombre']
        if 'tipo' in data:
            ubicacion.tipo = data['tipo']
        if 'piso' in data:
            ubicacion.piso = data['piso']
        if 'capacidad' in data:
            ubicacion.capacidad = data['capacidad']
        if 'descripcion' in data:
            ubicacion.descripcion = data['descripcion']
        if 'tiene_qr' in data:
            ubicacion.tiene_qr = data['tiene_qr']
        if 'activo' in data:
            ubicacion.activo = data['activo']
        
        ubicacion.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Ubicación actualizada exitosamente',
        })
    except Ubicacion.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ubicación no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@require_http_methods(["DELETE"])
@user_passes_test(es_admin, login_url='/login/')
@csrf_exempt
def api_ubicaciones_eliminar(request, ubicacion_id):
    """Marca una ubicación como inactiva (soft delete)"""
    try:
        ubicacion = Ubicacion.objects.get(id=ubicacion_id)
        ubicacion.activo = False
        ubicacion.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Ubicación eliminada exitosamente',
        })
    except Ubicacion.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Ubicación no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
