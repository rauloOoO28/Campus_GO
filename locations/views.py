"""
locations/views.py

Vistas públicas de la app locations:
  - resolver_qr: a la que apuntan los códigos QR
  - detalle_publico: misma vista pero sin registrar escaneo
  - api_ubicaciones_campus: endpoint JSON para alimentar el mapa
  - api_calcular_ruta: endpoint que devuelve la ruta entre 2 ubicaciones

CAMBIOS EN ESTA VERSIÓN:
  - El API devuelve también stats por categoría (incluyendo edificios y baños)
  - Nuevo endpoint /api/ruta/ para calcular rutas (Fase 1: línea inteligente)
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, Http404

from .models import Ubicacion, Campus, Edificio


# ============================================================
# VISTAS PÚBLICAS DE QR
# ============================================================
def resolver_qr(request, codigo):
    """
    Vista pública a la que apuntan los QR.
    URL: /qr/<codigo>/   ej: /qr/escom-entrada-principal/
    """
    ubicacion = get_object_or_404(Ubicacion, codigo=codigo, activo=True)

    if ubicacion.tiene_qr:
        ubicacion.codigo_qr.registrar_escaneo()

    return render(request, 'locations/detalle_publico.html', {
        'ubicacion': ubicacion,
        'desde_qr': True,
    })


def detalle_publico(request, codigo):
    """Misma vista que `resolver_qr` pero sin registrar escaneo."""
    ubicacion = get_object_or_404(Ubicacion, codigo=codigo, activo=True)
    return render(request, 'locations/detalle_publico.html', {
        'ubicacion': ubicacion,
        'desde_qr': False,
    })


# ============================================================
# API: UBICACIONES DEL CAMPUS
# ============================================================
def api_ubicaciones_campus(request, codigo_campus):
    """
    Endpoint JSON que devuelve todas las ubicaciones activas de un campus
    junto con estadísticas por categoría.

    URL: /api/campus/<codigo_campus>/ubicaciones/
    """
    campus = get_object_or_404(Campus, codigo=codigo_campus, activo=True)

    ubicaciones = campus.ubicaciones.filter(activo=True).select_related('edificio')

    # Centro del mapa: usar entrada principal como referencia
    if ubicaciones.exists():
        entrada_principal = ubicaciones.filter(tipo=Ubicacion.TIPO_ENTRADA).first()
        if entrada_principal:
            centro = [float(entrada_principal.latitud), float(entrada_principal.longitud)]
        else:
            primera = ubicaciones.first()
            centro = [float(primera.latitud), float(primera.longitud)]
    else:
        centro = [19.5043, -99.1467]  # ESCOM default

    # Stats por categoría
    stats = {
        'entrada':     ubicaciones.filter(tipo=Ubicacion.TIPO_ENTRADA).count(),
        'aula':        ubicaciones.filter(tipo=Ubicacion.TIPO_AULA).count(),
        'laboratorio': ubicaciones.filter(tipo=Ubicacion.TIPO_LABORATORIO).count(),
        'oficina':     ubicaciones.filter(tipo=Ubicacion.TIPO_OFICINA).count(),
        'servicio':    ubicaciones.filter(tipo=Ubicacion.TIPO_SERVICIO).count(),
        'baño':        ubicaciones.filter(tipo=Ubicacion.TIPO_BAÑO).count(),
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
# API: CALCULAR RUTA ENTRE 2 UBICACIONES
# ============================================================
def api_calcular_ruta(request):
    """
    Calcula y devuelve la ruta entre dos ubicaciones.

    URL: /api/ruta/?desde=<codigo>&hasta=<codigo>
    Ej:  /api/ruta/?desde=escom-entrada-principal&hasta=escom-entrada-posterior

    ⚠️ ESTADO ACTUAL: FASE 1 (línea inteligente)
    ─────────────────────────────────────────────────────────
    Por ahora devuelve una línea con puntos intermedios calculados
    geométricamente. NO sigue pasillos reales.

    🔜 FASE 2 (cuando NetworkX esté listo):
    ─────────────────────────────────────────────────────────
    Aquí debe ir la llamada a NetworkX para calcular la ruta real
    usando el grafo de nodos del campus. Algo así:

        import networkx as nx
        from .grafo import construir_grafo_campus

        G = construir_grafo_campus(origen.campus)
        nodos_ruta = nx.shortest_path(
            G,
            source=origen.nodo_id,
            target=destino.nodo_id,
            weight='distancia'
        )
        ruta_coords = [
            [G.nodes[n]['lat'], G.nodes[n]['lng']]
            for n in nodos_ruta
        ]

    Respuesta JSON:
    {
        "origen":  { codigo, nombre, lat, lng, tipo_label },
        "destino": { codigo, nombre, lat, lng, tipo_label },
        "ruta":    [[lat, lng], [lat, lng], ...],
        "stats":   { distancia_m, tiempo_min, pasos },
        "metodo":  "linea_inteligente"   // o "networkx_dijkstra" en Fase 2
    }
    """
    codigo_desde = request.GET.get('desde')
    codigo_hasta = request.GET.get('hasta')

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

    # ⚠️ FASE 1: Calcular ruta como línea con puntos intermedios "inteligentes"
    ruta_coords = _calcular_ruta_linea_inteligente(origen, destino)

    # Estadísticas estimadas
    distancia_m = _calcular_distancia_total(ruta_coords)
    tiempo_min = max(1, round(distancia_m / 80))   # ~80 m/min caminando
    pasos = round(distancia_m * 1.3)

    return JsonResponse({
        'origen': {
            'codigo': origen.codigo,
            'nombre': origen.nombre,
            'tipo':   origen.tipo,
            'tipo_label': origen.get_tipo_display(),
            'lat': float(origen.latitud),
            'lng': float(origen.longitud),
            'edificio': origen.edificio.nombre if origen.edificio else None,
        },
        'destino': {
            'codigo': destino.codigo,
            'nombre': destino.nombre,
            'tipo':   destino.tipo,
            'tipo_label': destino.get_tipo_display(),
            'lat': float(destino.latitud),
            'lng': float(destino.longitud),
            'edificio': destino.edificio.nombre if destino.edificio else None,
        },
        'ruta': ruta_coords,
        'stats': {
            'distancia_m': distancia_m,
            'tiempo_min':  tiempo_min,
            'pasos':       pasos,
        },
        'metodo': 'linea_inteligente',
        'instrucciones': _generar_instrucciones_basicas(origen, destino, distancia_m),
    })


# ============================================================
# FUNCIONES AUXILIARES
# (En Fase 2 se reemplazan por NetworkX)
# ============================================================
def _calcular_ruta_linea_inteligente(origen, destino):
    """
    Genera una ruta con puntos intermedios entre origen y destino.
    Crea un quiebre en forma de "L" para simular que va por pasillos.

    🔜 En Fase 2 esto se reemplaza por una consulta al grafo NetworkX.
    """
    lat1, lng1 = float(origen.latitud),  float(origen.longitud)
    lat2, lng2 = float(destino.latitud), float(destino.longitud)

    # Punto intermedio: avanza primero horizontal y luego vertical
    # (esto da el efecto de "doblar en esquina")
    punto_medio = [lat1, lng2]

    return [
        [lat1, lng1],
        punto_medio,
        [lat2, lng2],
    ]


def _calcular_distancia_total(coords):
    """Calcula la distancia total en metros usando fórmula de Haversine."""
    from math import radians, sin, cos, sqrt, atan2

    total = 0.0
    R = 6371000  # radio de la Tierra en metros

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


def _generar_instrucciones_basicas(origen, destino, distancia_m):
    """
    Genera instrucciones de navegación simples.
    🔜 En Fase 2 esto vendrá del grafo (cada arista tendrá su instrucción).
    """
    return [
        {
            'paso': 1,
            'texto': f'Sal de {origen.nombre}',
            'icono': 'bi-arrow-up-circle-fill',
        },
        {
            'paso': 2,
            'texto': 'Camina por el sendero principal del campus',
            'icono': 'bi-arrow-up',
            'distancia': f'{round(distancia_m * 0.6)} m',
        },
        {
            'paso': 3,
            'texto': 'Dobla y dirígete al edificio destino',
            'icono': 'bi-arrow-right',
            'distancia': f'{round(distancia_m * 0.4)} m',
        },
        {
            'paso': 4,
            'texto': f'Llegaste a {destino.nombre}',
            'icono': 'bi-flag-fill',
        },
    ]