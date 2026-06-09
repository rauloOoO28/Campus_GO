"""
locations/views_editor.py

Vistas del editor visual del grafo de rutas:
  - editor_grafo_view: pantalla con el mapa Leaflet para editar el grafo
  - api_editor_data:   devuelve nodos + aristas + ubicaciones del campus
  - api_crear_nodo:    crea un nodo nuevo (clic en el mapa)
  - api_actualizar_nodo: edita nombre/tipo/vinculación de un nodo
  - api_eliminar_nodo: borra un nodo (y sus aristas)
  - api_crear_arista:  conecta 2 nodos
  - api_eliminar_arista: borra una conexión

Todas las APIs requieren que el usuario esté autenticado como staff.
"""

import json
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Campus, Ubicacion, NodoGrafo, AristaGrafo


# ============================================================
# VISTA PRINCIPAL DEL EDITOR
# ============================================================
@staff_member_required
@ensure_csrf_cookie
def editor_grafo_view(request, codigo_campus):
    """
    Renderiza la pantalla del editor visual del grafo.
    Usa Leaflet para mostrar el mapa y permite agregar nodos/aristas
    con clics interactivos.
    """
    campus = get_object_or_404(Campus, codigo=codigo_campus)

    # Centro del mapa: usar entrada principal si existe, si no el centro del campus
    entrada = campus.ubicaciones.filter(
        tipo=Ubicacion.TIPO_ENTRADA, activo=True
    ).first()

    if entrada:
        centro = [float(entrada.latitud), float(entrada.longitud)]
    else:
        ubic = campus.ubicaciones.filter(activo=True).first()
        if ubic:
            centro = [float(ubic.latitud), float(ubic.longitud)]
        else:
            centro = [19.5043, -99.1467]  # ESCOM default

    return render(request, 'admin/locations/editor_grafo.html', {
        'campus': campus,
        'centro': centro,
        'opts': NodoGrafo._meta,
        'has_view_permission': True,
        # Contexto del admin para que se vea integrado
        'title': f'Editor de grafo · {campus.nombre}',
        'site_title': 'CampusGo',
        'site_header': 'Administración CampusGo',
    })


# ============================================================
# API: CARGAR DATOS DEL GRAFO
# ============================================================
@staff_member_required
def api_editor_data(request, codigo_campus):
    """
    Devuelve todos los datos necesarios para renderizar el editor:
      - nodos del grafo
      - aristas del grafo
      - ubicaciones que pueden vincularse (entradas, aulas, etc.)
    """
    campus = get_object_or_404(Campus, codigo=codigo_campus)

    nodos = campus.nodos.all().select_related('ubicacion')
    aristas = AristaGrafo.objects.filter(origen__campus=campus).select_related('origen', 'destino')
    ubicaciones = campus.ubicaciones.filter(activo=True)

    # Códigos de ubicaciones que YA tienen nodo vinculado
    ubicaciones_con_nodo = set(
        nodos.exclude(ubicacion__isnull=True).values_list('ubicacion_id', flat=True)
    )

    return JsonResponse({
        'campus': {
            'codigo': campus.codigo,
            'nombre': campus.nombre,
        },
        'tipos_nodo': [
            {'value': v, 'label': l} for v, l in NodoGrafo.TIPOS
        ],
        'tipos_arista': [
            {'value': v, 'label': l} for v, l in AristaGrafo.TIPOS
        ],
        'nodos': [
            {
                'id': n.id,
                'codigo': n.codigo,
                'nombre': n.nombre,
                'tipo': n.tipo,
                'tipo_label': n.get_tipo_display(),
                'lat': float(n.latitud),
                'lng': float(n.longitud),
                'ubicacion_id': n.ubicacion_id,
                'ubicacion_nombre': n.ubicacion.nombre if n.ubicacion else None,
                'activo': n.activo,
            }
            for n in nodos
        ],
        'aristas': [
            {
                'id': a.id,
                'origen_id': a.origen_id,
                'destino_id': a.destino_id,
                'origen_nombre': a.origen.nombre,
                'destino_nombre': a.destino.nombre,
                'distancia_m': float(a.distancia_m),
                'tipo': a.tipo,
                'tipo_label': a.get_tipo_display(),
                'accesible': a.accesible,
                'bidireccional': a.bidireccional,
            }
            for a in aristas
        ],
        'ubicaciones_disponibles': [
            {
                'id': u.id,
                'nombre': u.nombre,
                'tipo': u.tipo,
                'tipo_label': u.get_tipo_display(),
                'tiene_nodo': u.id in ubicaciones_con_nodo,
            }
            for u in ubicaciones
        ]
    })


# ============================================================
# API: CRUD DE NODOS
# ============================================================
@staff_member_required
@require_http_methods(['POST'])
def api_crear_nodo(request, codigo_campus):
    """Crea un nodo nuevo. Espera JSON con: lat, lng, nombre, tipo, [ubicacion_id]."""
    campus = get_object_or_404(Campus, codigo=codigo_campus)
    data = json.loads(request.body)

    try:
        ubicacion_id = data.get('ubicacion_id')
        ubicacion = None
        if ubicacion_id:
            ubicacion = Ubicacion.objects.get(id=ubicacion_id, campus=campus)
            # Verificar que la ubicación no tenga ya un nodo
            if hasattr(ubicacion, 'nodo_grafo') and ubicacion.nodo_grafo:
                return JsonResponse({
                    'error': f'La ubicación "{ubicacion.nombre}" ya tiene un nodo vinculado.'
                }, status=400)

        nodo = NodoGrafo.objects.create(
            campus=campus,
            nombre=data.get('nombre', 'Nodo nuevo'),
            tipo=data.get('tipo', NodoGrafo.TIPO_PASILLO),
            latitud=data['lat'],
            longitud=data['lng'],
            ubicacion=ubicacion,
        )

        return JsonResponse({
            'exito': True,
            'nodo': {
                'id': nodo.id,
                'codigo': nodo.codigo,
                'nombre': nodo.nombre,
                'tipo': nodo.tipo,
                'tipo_label': nodo.get_tipo_display(),
                'lat': float(nodo.latitud),
                'lng': float(nodo.longitud),
                'ubicacion_id': nodo.ubicacion_id,
                'ubicacion_nombre': nodo.ubicacion.nombre if nodo.ubicacion else None,
            }
        })
    except Ubicacion.DoesNotExist:
        return JsonResponse({'error': 'Ubicación no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@staff_member_required
@require_http_methods(['POST'])
def api_actualizar_nodo(request, codigo_campus, nodo_id):
    """Actualiza un nodo (nombre, tipo, vinculación, posición)."""
    campus = get_object_or_404(Campus, codigo=codigo_campus)
    nodo = get_object_or_404(NodoGrafo, id=nodo_id, campus=campus)
    data = json.loads(request.body)

    try:
        if 'nombre' in data:
            nodo.nombre = data['nombre']
        if 'tipo' in data:
            nodo.tipo = data['tipo']
        if 'lat' in data:
            nodo.latitud = data['lat']
        if 'lng' in data:
            nodo.longitud = data['lng']

        if 'ubicacion_id' in data:
            nuevo_ubicacion_id = data['ubicacion_id']
            if nuevo_ubicacion_id:
                ubicacion = Ubicacion.objects.get(id=nuevo_ubicacion_id, campus=campus)
                # Validar que no tenga ya otro nodo (excepto este mismo)
                if hasattr(ubicacion, 'nodo_grafo') and ubicacion.nodo_grafo \
                        and ubicacion.nodo_grafo.id != nodo.id:
                    return JsonResponse({
                        'error': f'La ubicación "{ubicacion.nombre}" ya tiene otro nodo vinculado.'
                    }, status=400)
                nodo.ubicacion = ubicacion
            else:
                nodo.ubicacion = None

        nodo.save()

        # Si se cambió la posición, recalcular las distancias de las aristas conectadas
        if 'lat' in data or 'lng' in data:
            aristas_afectadas = list(nodo.aristas_salida.all()) + list(nodo.aristas_entrada.all())
            for arista in aristas_afectadas:
                arista.distancia_m = arista._calcular_distancia_haversine()
                arista.save()

        return JsonResponse({
            'exito': True,
            'nodo': {
                'id': nodo.id,
                'codigo': nodo.codigo,
                'nombre': nodo.nombre,
                'tipo': nodo.tipo,
                'tipo_label': nodo.get_tipo_display(),
                'lat': float(nodo.latitud),
                'lng': float(nodo.longitud),
                'ubicacion_id': nodo.ubicacion_id,
                'ubicacion_nombre': nodo.ubicacion.nombre if nodo.ubicacion else None,
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@staff_member_required
@require_http_methods(['POST', 'DELETE'])
def api_eliminar_nodo(request, codigo_campus, nodo_id):
    """Elimina un nodo (y sus aristas asociadas por CASCADE)."""
    campus = get_object_or_404(Campus, codigo=codigo_campus)
    nodo = get_object_or_404(NodoGrafo, id=nodo_id, campus=campus)

    # Contar aristas que se borrarán también
    aristas_borradas = (
        nodo.aristas_salida.count() + nodo.aristas_entrada.count()
    )
    nombre = nodo.nombre
    nodo.delete()

    return JsonResponse({
        'exito': True,
        'mensaje': f'Nodo "{nombre}" eliminado.',
        'aristas_borradas': aristas_borradas,
    })


# ============================================================
# API: CRUD DE ARISTAS
# ============================================================
@staff_member_required
@require_http_methods(['POST'])
def api_crear_arista(request, codigo_campus):
    """
    Crea una arista entre dos nodos.
    Espera JSON: { origen_id, destino_id, tipo?, accesible?, bidireccional? }
    """
    campus = get_object_or_404(Campus, codigo=codigo_campus)
    data = json.loads(request.body)

    try:
        origen = NodoGrafo.objects.get(id=data['origen_id'], campus=campus)
        destino = NodoGrafo.objects.get(id=data['destino_id'], campus=campus)

        if origen.id == destino.id:
            return JsonResponse({
                'error': 'No puedes conectar un nodo consigo mismo.'
            }, status=400)

        # Verificar si ya existe la arista (en cualquier dirección)
        existente = AristaGrafo.objects.filter(
            origen__in=[origen, destino],
            destino__in=[origen, destino],
        ).first()

        if existente:
            return JsonResponse({
                'error': f'Ya existe una conexión entre "{origen.nombre}" y "{destino.nombre}".'
            }, status=400)

        arista = AristaGrafo.objects.create(
            origen=origen,
            destino=destino,
            tipo=data.get('tipo', AristaGrafo.TIPO_SENDERO),
            accesible=data.get('accesible', True),
            bidireccional=data.get('bidireccional', True),
        )

        return JsonResponse({
            'exito': True,
            'arista': {
                'id': arista.id,
                'origen_id': arista.origen_id,
                'destino_id': arista.destino_id,
                'origen_nombre': arista.origen.nombre,
                'destino_nombre': arista.destino.nombre,
                'distancia_m': float(arista.distancia_m),
                'tipo': arista.tipo,
                'tipo_label': arista.get_tipo_display(),
                'accesible': arista.accesible,
                'bidireccional': arista.bidireccional,
            }
        })
    except NodoGrafo.DoesNotExist:
        return JsonResponse({'error': 'Nodo no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@staff_member_required
@require_http_methods(['POST', 'DELETE'])
def api_eliminar_arista(request, codigo_campus, arista_id):
    """Elimina una arista."""
    campus = get_object_or_404(Campus, codigo=codigo_campus)
    arista = get_object_or_404(
        AristaGrafo, id=arista_id, origen__campus=campus
    )
    descripcion = str(arista)
    arista.delete()
    return JsonResponse({
        'exito': True,
        'mensaje': f'Conexión eliminada: {descripcion}',
    })