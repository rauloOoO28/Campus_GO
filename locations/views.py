"""
locations/views.py

CAMBIO PRINCIPAL EN ESTA VERSIÓN:
  - api_calcular_ruta ahora usa NetworkX si hay grafo construido
  - Si no hay grafo (o falla), cae al método "línea inteligente" como fallback
  - Esto permite migrar de Fase 1 → Fase 2 sin romper nada
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404

from .models import Ubicacion, Campus, Edificio
from .grafo import calcular_ruta_entre_ubicaciones, construir_grafo_campus, generar_instrucciones_desde_ruta


# ============================================================
# VISTAS PÚBLICAS DE QR
# ============================================================
def resolver_qr(request, codigo):
    ubicacion = get_object_or_404(Ubicacion, codigo=codigo, activo=True)
    if ubicacion.tiene_qr:
        ubicacion.codigo_qr.registrar_escaneo()
    return render(request, 'locations/detalle_publico.html', {
        'ubicacion': ubicacion,
        'desde_qr': True,
    })


def detalle_publico(request, codigo):
    ubicacion = get_object_or_404(Ubicacion, codigo=codigo, activo=True)
    return render(request, 'locations/detalle_publico.html', {
        'ubicacion': ubicacion,
        'desde_qr': False,
    })


# ============================================================
# API: UBICACIONES DEL CAMPUS
# ============================================================
def api_ubicaciones_campus(request, codigo_campus):
    campus = get_object_or_404(Campus, codigo=codigo_campus, activo=True)
    ubicaciones = campus.ubicaciones.filter(activo=True).select_related('edificio')

    if ubicaciones.exists():
        entrada_principal = ubicaciones.filter(tipo=Ubicacion.TIPO_ENTRADA).first()
        if entrada_principal:
            centro = [float(entrada_principal.latitud), float(entrada_principal.longitud)]
        else:
            primera = ubicaciones.first()
            centro = [float(primera.latitud), float(primera.longitud)]
    else:
        centro = [19.5043, -99.1467]

    stats = {
        'entrada':     ubicaciones.filter(tipo=Ubicacion.TIPO_ENTRADA).count(),
        'aula':        ubicaciones.filter(tipo=Ubicacion.TIPO_AULA).count(),
        'laboratorio': ubicaciones.filter(tipo=Ubicacion.TIPO_LABORATORIO).count(),
        'oficina':     ubicaciones.filter(tipo=Ubicacion.TIPO_OFICINA).count(),
        'servicio':    ubicaciones.filter(tipo=Ubicacion.TIPO_SERVICIO).count(),
        'bano':        ubicaciones.filter(tipo=Ubicacion.TIPO_BANO).count(),
        'edificios':   campus.edificios.count(),
        'total':       ubicaciones.count(),
    }

    data = {
        'campus': {
            'codigo': campus.codigo,
            'nombre': campus.nombre,
            'direccion': campus.direccion,
            'centro': centro,
        },
        'stats': stats,
        'ubicaciones': [
            {
                'id': u.id,
                'codigo': u.codigo,
                'nombre': u.nombre,
                'tipo': u.tipo,
                'tipo_label': u.get_tipo_display(),
                'lat': float(u.latitud),
                'lng': float(u.longitud),
                'edificio': u.edificio.nombre if u.edificio else None,
                'piso': u.piso,
                'descripcion': u.descripcion,
                'url_detalle': u.get_absolute_url(),
            }
            for u in ubicaciones
        ]
    }
    return JsonResponse(data)


# ============================================================
# API: CALCULAR RUTA  ⭐ AHORA CON NETWORKX
# ============================================================
def api_calcular_ruta(request):
    """
    Calcula la ruta entre dos ubicaciones.

    Estrategia:
      1. Intenta usar NetworkX (Fase 2) con el grafo del campus.
      2. Si no hay grafo aún o algo falla, cae a "línea inteligente" (Fase 1).

    Parámetros GET:
      - desde: código de la ubicación origen
      - hasta: código de la ubicación destino
      - accesible: 'true' para forzar ruta sin escaleras (opcional)
    """
    codigo_desde = request.GET.get('desde')
    codigo_hasta = request.GET.get('hasta')
    solo_accesible = request.GET.get('accesible', '').lower() == 'true'

    if not codigo_desde or not codigo_hasta:
        return JsonResponse({
            'error': 'Se requieren los parámetros "desde" y "hasta"'
        }, status=400)

    try:
        origen = Ubicacion.objects.get(codigo=codigo_desde, activo=True)
        destino = Ubicacion.objects.get(codigo=codigo_hasta, activo=True)
    except Ubicacion.DoesNotExist:
        raise Http404("Ubicación no encontrada")

    if origen.campus_id != destino.campus_id:
        return JsonResponse({
            'error': 'Origen y destino deben ser del mismo campus'
        }, status=400)

    # ============================================================
    # 🎯 INTENTAR CON NETWORKX (Fase 2)
    # ============================================================
    resultado_grafo = calcular_ruta_entre_ubicaciones(
        origen, destino, solo_accesible=solo_accesible
    )

    if resultado_grafo['exito']:
        # Generar instrucciones detalladas a partir de los nodos
        G = construir_grafo_campus(origen.campus)
        instrucciones = generar_instrucciones_desde_ruta(
            G, resultado_grafo['ruta_nodos'], origen, destino
        )

        distancia_m = resultado_grafo['distancia_m']
        tiempo_min = max(1, round(distancia_m / 80))
        pasos = round(distancia_m * 1.3)

        return JsonResponse({
            'origen':  _serializar_ubicacion(origen),
            'destino': _serializar_ubicacion(destino),
            'ruta':    resultado_grafo['ruta_coords'],
            'stats': {
                'distancia_m': distancia_m,
                'tiempo_min':  tiempo_min,
                'pasos':       pasos,
            },
            'metodo': 'networkx_dijkstra',
            'instrucciones': instrucciones,
            'accesible':    solo_accesible,
            'nodos_visitados': resultado_grafo.get('numero_pasos', 0) + 1,
        })

    # ============================================================
    # ⚠️ FALLBACK: línea inteligente (Fase 1)
    # ============================================================
    # Si llegamos aquí es porque NetworkX falló (no hay grafo aún, no hay nodos
    # vinculados, etc.). Caemos al método anterior para que la app siga funcionando.

    ruta_coords = _calcular_ruta_linea_inteligente(origen, destino)
    distancia_m = _calcular_distancia_total(ruta_coords)
    tiempo_min = max(1, round(distancia_m / 80))
    pasos = round(distancia_m * 1.3)

    return JsonResponse({
        'origen':  _serializar_ubicacion(origen),
        'destino': _serializar_ubicacion(destino),
        'ruta':    ruta_coords,
        'stats': {
            'distancia_m': distancia_m,
            'tiempo_min':  tiempo_min,
            'pasos':       pasos,
        },
        'metodo':        'linea_inteligente',
        'instrucciones': _instrucciones_basicas_fallback(origen, destino, distancia_m),
        'fallback_reason': resultado_grafo.get('error', 'Grafo no disponible'),
    })


# ============================================================
# AUXILIARES
# ============================================================
def _serializar_ubicacion(u):
    return {
        'codigo': u.codigo,
        'nombre': u.nombre,
        'tipo':   u.tipo,
        'tipo_label': u.get_tipo_display(),
        'lat': float(u.latitud),
        'lng': float(u.longitud),
        'edificio': u.edificio.nombre if u.edificio else None,
    }


def _calcular_ruta_linea_inteligente(origen, destino):
    """⚠️ FALLBACK Fase 1: línea en L. Solo se usa si NetworkX no tiene grafo."""
    lat1, lng1 = float(origen.latitud),  float(origen.longitud)
    lat2, lng2 = float(destino.latitud), float(destino.longitud)
    punto_medio = [lat1, lng2]
    return [[lat1, lng1], punto_medio, [lat2, lng2]]


def _calcular_distancia_total(coords):
    from math import radians, sin, cos, sqrt, atan2
    total = 0.0
    R = 6371000
    for i in range(len(coords) - 1):
        lat1, lng1 = coords[i]
        lat2, lng2 = coords[i + 1]
        dlat = radians(lat2 - lat1)
        dlng = radians(lng2 - lng1)
        a = (sin(dlat / 2) ** 2 +
             cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        total += R * c
    return round(total)


def _instrucciones_basicas_fallback(origen, destino, distancia_m):
    return [
        {'paso': 1, 'texto': f'Sal de {origen.nombre}',                 'icono': 'bi-arrow-up-circle-fill'},
        {'paso': 2, 'texto': 'Camina por el sendero principal',         'icono': 'bi-arrow-up',
         'distancia': f'{round(distancia_m * 0.6)} m'},
        {'paso': 3, 'texto': 'Dirígete al edificio destino',            'icono': 'bi-arrow-right',
         'distancia': f'{round(distancia_m * 0.4)} m'},
        {'paso': 4, 'texto': f'Llegaste a {destino.nombre}',            'icono': 'bi-flag-fill'},
    ]