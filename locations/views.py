"""
locations/views.py

Vistas públicas de la app locations:
  - resolver_qr: a la que apuntan los códigos QR
  - detalle_publico: misma vista pero sin registrar escaneo
  - api_ubicaciones_campus: endpoint JSON para alimentar el mapa
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

from .models import Ubicacion, Campus


def resolver_qr(request, codigo):
    """
    Vista pública a la que apuntan los QR.

    Flujo:
      1. Usuario escanea QR con la cámara → abre /qr/<codigo>/ en el navegador
      2. Esta vista busca la ubicación por su slug
      3. Registra el escaneo (incrementa contador)
      4. Renderiza la página de detalle con banner de bienvenida

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
    """
    Misma vista que `resolver_qr` pero sin registrar escaneo
    (uso interno, navegación normal por la app).
    """
    ubicacion = get_object_or_404(Ubicacion, codigo=codigo, activo=True)
    return render(request, 'locations/detalle_publico.html', {
        'ubicacion': ubicacion,
        'desde_qr': False,
    })


# ============================================================
# API JSON
# ============================================================
def api_ubicaciones_campus(request, codigo_campus):
    """
    Endpoint JSON que devuelve todas las ubicaciones activas de un campus.
    Alimenta el mapa Leaflet del frontend.

    URL: /api/campus/<codigo_campus>/ubicaciones/
    Ej:  /api/campus/escom-ipn/ubicaciones/

    Respuesta:
    {
        "campus": {
            "codigo": "escom-ipn",
            "nombre": "ESCOM IPN",
            "centro": [19.5043, -99.1467]
        },
        "ubicaciones": [
            {
                "id": 1,
                "codigo": "escom-entrada-principal",
                "nombre": "Entrada Principal ESCOM",
                "tipo": "entrada",
                "tipo_label": "Entrada",
                "lat": 19.5043270,
                "lng": -99.1466870,
                "edificio": null,
                "piso": 0,
                "descripcion": "...",
                "url_detalle": "/ubicacion/escom-entrada-principal/"
            },
            ...
        ]
    }
    """
    campus = get_object_or_404(Campus, codigo=codigo_campus, activo=True)

    ubicaciones = campus.ubicaciones.filter(activo=True).select_related('edificio')

    # Calcular el centro del campus como promedio de las ubicaciones,
    # o usar el de la primera entrada si existe
    if ubicaciones.exists():
        entrada_principal = ubicaciones.filter(tipo=Ubicacion.TIPO_ENTRADA).first()
        if entrada_principal:
            centro = [float(entrada_principal.latitud), float(entrada_principal.longitud)]
        else:
            primera = ubicaciones.first()
            centro = [float(primera.latitud), float(primera.longitud)]
    else:
        # Centro de ESCOM por defecto si no hay ubicaciones
        centro = [19.5043, -99.1467]

    data = {
        'campus': {
            'codigo': campus.codigo,
            'nombre': campus.nombre,
            'direccion': campus.direccion,
            'centro': centro,
        },
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