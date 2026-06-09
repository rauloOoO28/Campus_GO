"""
locations/grafo.py

Motor de cálculo de rutas con NetworkX.

Este módulo construye un grafo dirigido (o no dirigido) a partir de los
modelos NodoGrafo y AristaGrafo de la BD, y aplica el algoritmo Dijkstra
para encontrar la ruta más corta entre dos puntos.

Uso típico:
    from locations.grafo import calcular_ruta_entre_ubicaciones
    resultado = calcular_ruta_entre_ubicaciones(ubicacion_origen, ubicacion_destino)
"""

import networkx as nx
from math import radians, sin, cos, sqrt, atan2

from .models import NodoGrafo, AristaGrafo, Ubicacion


# ============================================================
# CONSTRUCCIÓN DEL GRAFO
# ============================================================
def construir_grafo_campus(campus):
    """
    Construye un grafo NetworkX a partir de los nodos y aristas
    de un campus específico.

    Returns:
        nx.Graph (no dirigido) con:
          - nodes  → códigos de los nodos
          - lat, lng en data['lat'], data['lng']
          - aristas con weight=distancia_m
    """
    G = nx.Graph()

    # Cargar TODOS los nodos activos del campus
    nodos = NodoGrafo.objects.filter(campus=campus, activo=True).select_related('ubicacion')

    for nodo in nodos:
        G.add_node(
            nodo.codigo,
            lat=float(nodo.latitud),
            lng=float(nodo.longitud),
            nombre=nodo.nombre,
            tipo=nodo.tipo,
            ubicacion_codigo=nodo.ubicacion.codigo if nodo.ubicacion else None,
        )

    # Cargar TODAS las aristas activas del campus
    aristas = AristaGrafo.objects.filter(
        origen__campus=campus,
        activo=True,
    ).select_related('origen', 'destino')

    for arista in aristas:
        G.add_edge(
            arista.origen.codigo,
            arista.destino.codigo,
            weight=float(arista.distancia_m),
            tipo=arista.tipo,
            accesible=arista.accesible,
        )

    return G


# ============================================================
# CÁLCULO DE RUTAS
# ============================================================
def calcular_ruta_entre_ubicaciones(ubicacion_origen, ubicacion_destino, solo_accesible=False):
    """
    Calcula la ruta más corta entre dos UBICACIONES usando NetworkX + Dijkstra.

    Args:
        ubicacion_origen: instancia de Ubicacion
        ubicacion_destino: instancia de Ubicacion
        solo_accesible: si True, ignora aristas con accesible=False (escaleras)

    Returns:
        dict con:
          - 'exito': bool
          - 'ruta_coords': [[lat, lng], ...] lista para Leaflet
          - 'ruta_nodos': [codigos de nodos en el camino]
          - 'distancia_m': float
          - 'metodo': 'networkx_dijkstra' (vs 'linea_inteligente' del fallback)
          - 'error': str si exito=False

    Si alguna ubicación NO tiene nodo vinculado, busca el nodo más cercano
    automáticamente para que funcione aunque el grafo no esté 100% conectado.
    """
    if ubicacion_origen.campus_id != ubicacion_destino.campus_id:
        return _error("Origen y destino deben ser del mismo campus")

    campus = ubicacion_origen.campus

    # Construir el grafo
    G = construir_grafo_campus(campus)

    if G.number_of_nodes() == 0:
        return _error(
            "El campus aún no tiene grafo de rutas. "
            "Agrega nodos y aristas desde el admin."
        )

    # Filtrar aristas no accesibles si se pidió
    if solo_accesible:
        aristas_no_accesibles = [
            (u, v) for u, v, d in G.edges(data=True)
            if not d.get('accesible', True)
        ]
        G.remove_edges_from(aristas_no_accesibles)

    # Buscar el nodo correspondiente a cada ubicación
    nodo_origen = _encontrar_nodo_para_ubicacion(ubicacion_origen, G)
    nodo_destino = _encontrar_nodo_para_ubicacion(ubicacion_destino, G)

    if not nodo_origen:
        return _error(
            f"No hay nodo del grafo vinculado a '{ubicacion_origen.nombre}'. "
            f"Crea uno desde el admin y vincúlalo a esta ubicación."
        )
    if not nodo_destino:
        return _error(
            f"No hay nodo del grafo vinculado a '{ubicacion_destino.nombre}'."
        )

    # Calcular la ruta más corta
    try:
        codigos_ruta = nx.shortest_path(
            G,
            source=nodo_origen,
            target=nodo_destino,
            weight='weight',
        )
    except nx.NetworkXNoPath:
        return _error(
            "No existe una ruta conectada entre estos dos puntos. "
            "Verifica que el grafo del campus tenga aristas que los conecten."
        )
    except nx.NodeNotFound as e:
        return _error(f"Nodo no encontrado: {e}")

    # Convertir códigos de nodos a coordenadas para Leaflet
    ruta_coords = [
        [G.nodes[codigo]['lat'], G.nodes[codigo]['lng']]
        for codigo in codigos_ruta
    ]

    # Calcular distancia total
    distancia_total = sum(
        G[codigos_ruta[i]][codigos_ruta[i + 1]]['weight']
        for i in range(len(codigos_ruta) - 1)
    )

    return {
        'exito': True,
        'ruta_coords': ruta_coords,
        'ruta_nodos': codigos_ruta,
        'distancia_m': round(distancia_total, 2),
        'metodo': 'networkx_dijkstra',
        'numero_pasos': len(codigos_ruta) - 1,  # cantidad de tramos
    }


# ============================================================
# AUXILIARES
# ============================================================
def _encontrar_nodo_para_ubicacion(ubicacion, G):
    """
    Devuelve el código del nodo en el grafo que corresponde a la ubicación.

    Estrategia:
      1. Si la ubicación tiene un nodo_grafo vinculado, usar ese.
      2. Si no, buscar el nodo más cercano geográficamente.
      3. Si no hay nodos en el grafo, devolver None.
    """
    # Estrategia 1: nodo vinculado directamente
    if hasattr(ubicacion, 'nodo_grafo') and ubicacion.nodo_grafo and ubicacion.nodo_grafo.activo:
        codigo = ubicacion.nodo_grafo.codigo
        if codigo in G:
            return codigo

    # Estrategia 2: nodo más cercano por distancia Haversine
    if G.number_of_nodes() == 0:
        return None

    lat_ubi = float(ubicacion.latitud)
    lng_ubi = float(ubicacion.longitud)

    mejor_codigo = None
    mejor_distancia = float('inf')

    for codigo, data in G.nodes(data=True):
        d = _distancia_haversine(lat_ubi, lng_ubi, data['lat'], data['lng'])
        if d < mejor_distancia:
            mejor_distancia = d
            mejor_codigo = codigo

    return mejor_codigo


def _distancia_haversine(lat1, lng1, lat2, lng2):
    """Distancia en metros entre dos coordenadas geográficas."""
    R = 6371000
    rlat1, rlng1 = radians(lat1), radians(lng1)
    rlat2, rlng2 = radians(lat2), radians(lng2)
    dlat = rlat2 - rlat1
    dlng = rlng2 - rlng1
    a = sin(dlat / 2) ** 2 + cos(rlat1) * cos(rlat2) * sin(dlng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def _error(mensaje):
    """Helper para devolver un resultado de error consistente."""
    return {
        'exito': False,
        'error': mensaje,
        'metodo': None,
    }


# ============================================================
# GENERAR INSTRUCCIONES PASO A PASO
# ============================================================
def generar_instrucciones_desde_ruta(G, codigos_ruta, ubicacion_origen, ubicacion_destino):
    """
    Genera instrucciones de navegación legibles a partir de la lista de nodos.

    Por ahora son básicas: "Camina de X a Y, distancia Z metros".
    Más adelante se pueden enriquecer con direcciones (norte, gira a la derecha, etc.)
    """
    instrucciones = [
        {
            'paso': 1,
            'texto': f'Sal de {ubicacion_origen.nombre}',
            'icono': 'bi-arrow-up-circle-fill',
        }
    ]

    paso_num = 2
    for i in range(len(codigos_ruta) - 1):
        nodo_actual = G.nodes[codigos_ruta[i]]
        nodo_siguiente = G.nodes[codigos_ruta[i + 1]]
        arista = G[codigos_ruta[i]][codigos_ruta[i + 1]]
        distancia = arista['weight']

        if arista.get('tipo') == AristaGrafo.TIPO_ESCALERA:
            texto = f"Toma las escaleras hacia {nodo_siguiente['nombre']}"
            icono = 'bi-stairs'
        else:
            texto = f"Camina hasta {nodo_siguiente['nombre']}"
            icono = 'bi-arrow-up'

        instrucciones.append({
            'paso': paso_num,
            'texto': texto,
            'distancia': f'{round(distancia)} m',
            'icono': icono,
        })
        paso_num += 1

    instrucciones.append({
        'paso': paso_num,
        'texto': f'Llegaste a {ubicacion_destino.nombre}',
        'icono': 'bi-flag-fill',
    })

    return instrucciones