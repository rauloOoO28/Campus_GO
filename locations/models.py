"""
locations/models.py

Modelos para CampusGo:
  - Campus, Edificio, Ubicacion (lugares de interés con QR)
  - CodigoQR (códigos QR de las ubicaciones)
  - NodoGrafo, AristaGrafo (grafo de rutas del campus para NetworkX) ⭐ NUEVO
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


# ============================================================
# CAMPUS
# ============================================================
class Campus(models.Model):
    codigo = models.SlugField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, blank=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Campus"
        verbose_name_plural = "Campus"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


# ============================================================
# EDIFICIO
# ============================================================
class Edificio(models.Model):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='edificios')
    codigo = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    pisos = models.PositiveSmallIntegerField(default=1)

    class Meta:
        verbose_name = "Edificio"
        verbose_name_plural = "Edificios"
        ordering = ['campus', 'codigo']
        unique_together = [['campus', 'codigo']]

    def __str__(self):
        return f"{self.campus.codigo.upper()} · Edif. {self.codigo} - {self.nombre}"


# ============================================================
# UBICACIÓN
# ============================================================
class Ubicacion(models.Model):
    TIPO_ENTRADA     = 'entrada'
    TIPO_AULA        = 'aula'
    TIPO_LABORATORIO = 'laboratorio'
    TIPO_OFICINA     = 'oficina'
    TIPO_SERVICIO    = 'servicio'
    TIPO_BANO        = 'bano'

    TIPOS = [
        (TIPO_ENTRADA,     'Entrada'),
        (TIPO_AULA,        'Aula'),
        (TIPO_LABORATORIO, 'Laboratorio'),
        (TIPO_OFICINA,     'Oficina'),
        (TIPO_SERVICIO,    'Servicio (cafetería, biblioteca, etc.)'),
        (TIPO_BANO,        'Baño'),
    ]

    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='ubicaciones')
    edificio = models.ForeignKey(
        Edificio, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ubicaciones'
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    codigo = models.SlugField(max_length=80, unique=True)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=7)
    longitud = models.DecimalField(max_digits=10, decimal_places=7)
    piso = models.IntegerField(default=0)
    capacidad = models.PositiveIntegerField(null=True, blank=True)
    horario = models.CharField(max_length=200, blank=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"
        ordering = ['campus', 'tipo', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    def save(self, *args, **kwargs):
        if not self.codigo:
            base = f"{self.campus.codigo}-{self.tipo}-{self.nombre}"
            self.codigo = slugify(base)[:80]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('locations:detalle_publico', kwargs={'codigo': self.codigo})

    @property
    def tiene_qr(self):
        return hasattr(self, 'codigo_qr')


# ============================================================
# CÓDIGO QR
# ============================================================
def qr_upload_path(instance, filename):
    return f"qrs/{instance.ubicacion.codigo}.png"


class CodigoQR(models.Model):
    ubicacion = models.OneToOneField(Ubicacion, on_delete=models.CASCADE, related_name='codigo_qr')
    imagen = models.ImageField(upload_to=qr_upload_path, blank=True)
    url_destino = models.URLField(max_length=500)
    escaneos = models.PositiveIntegerField(default=0)
    creado = models.DateTimeField(auto_now_add=True)
    ultimo_escaneo = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Código QR"
        verbose_name_plural = "Códigos QR"
        ordering = ['-creado']

    def __str__(self):
        return f"QR de {self.ubicacion.nombre}"

    def registrar_escaneo(self):
        from django.utils import timezone
        self.escaneos += 1
        self.ultimo_escaneo = timezone.now()
        self.save(update_fields=['escaneos', 'ultimo_escaneo'])


# ============================================================
# ⭐ NUEVO: GRAFO DE RUTAS
# ============================================================
class NodoGrafo(models.Model):
    """
    Punto físico del campus que forma parte del grafo de rutas.

    Hay 2 tipos de nodos:
      - Nodos VINCULADOS a una Ubicación (entradas, edificios, etc.)
      - Nodos AUXILIARES (cruces de pasillo, plazas, sin Ubicación asociada)

    NetworkX usa estos nodos + las aristas para calcular rutas con Dijkstra.
    """

    TIPO_ENTRADA  = 'entrada'      # Puerta del campus
    TIPO_PASILLO  = 'pasillo'      # Punto intermedio en un sendero
    TIPO_CRUCE    = 'cruce'        # Intersección de pasillos
    TIPO_PLAZA    = 'plaza'        # Plaza/explanada (cruce abierto)
    TIPO_EDIFICIO = 'edificio'     # Entrada a un edificio
    TIPO_ESCALERA = 'escalera'     # Punto de cambio de piso

    TIPOS = [
        (TIPO_ENTRADA,  'Entrada del campus'),
        (TIPO_PASILLO,  'Pasillo'),
        (TIPO_CRUCE,    'Cruce'),
        (TIPO_PLAZA,    'Plaza / Explanada'),
        (TIPO_EDIFICIO, 'Entrada a edificio'),
        (TIPO_ESCALERA, 'Escalera'),
    ]

    campus = models.ForeignKey(
        Campus, on_delete=models.CASCADE, related_name='nodos'
    )
    codigo = models.SlugField(
        max_length=80, unique=True,
        help_text="Identificador único del nodo (ej. 'escom-plaza-central')"
    )
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS, default=TIPO_PASILLO)

    latitud = models.DecimalField(max_digits=10, decimal_places=7)
    longitud = models.DecimalField(max_digits=10, decimal_places=7)

    # Vinculación opcional a una Ubicación de interés
    ubicacion = models.OneToOneField(
        Ubicacion, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='nodo_grafo',
        help_text="Vincula este nodo a una Ubicación (entrada, edificio) para que las rutas la usen automáticamente"
    )

    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Nodo del grafo"
        verbose_name_plural = "Nodos del grafo"
        ordering = ['campus', 'codigo']

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"

    def save(self, *args, **kwargs):
        if not self.codigo:
            base = f"{self.campus.codigo}-nodo-{self.nombre}"
            self.codigo = slugify(base)[:80]
        super().save(*args, **kwargs)

    @property
    def coords(self):
        """Tupla (lat, lng) lista para Leaflet o NetworkX."""
        return (float(self.latitud), float(self.longitud))


class AristaGrafo(models.Model):
    """
    Conexión entre 2 nodos del grafo. Representa un camino físico
    (pasillo, sendero, escalera) por donde se puede caminar.

    Es no-dirigida por defecto (bidireccional).
    NetworkX usa la distancia_m como peso para Dijkstra.
    """

    TIPO_PASILLO  = 'pasillo'
    TIPO_SENDERO  = 'sendero'
    TIPO_ESCALERA = 'escalera'
    TIPO_PLAZA    = 'plaza'

    TIPOS = [
        (TIPO_PASILLO,  'Pasillo cerrado'),
        (TIPO_SENDERO,  'Sendero exterior'),
        (TIPO_ESCALERA, 'Escalera'),
        (TIPO_PLAZA,    'Cruce de plaza'),
    ]

    origen = models.ForeignKey(
        NodoGrafo, on_delete=models.CASCADE, related_name='aristas_salida'
    )
    destino = models.ForeignKey(
        NodoGrafo, on_delete=models.CASCADE, related_name='aristas_entrada'
    )
    distancia_m = models.DecimalField(
        max_digits=8, decimal_places=2,
        help_text="Distancia en metros (se calcula automática al guardar)"
    )
    tipo = models.CharField(max_length=20, choices=TIPOS, default=TIPO_SENDERO)
    accesible = models.BooleanField(
        default=True,
        help_text="¿Es accesible para silla de ruedas? (sin escaleras)"
    )
    bidireccional = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Arista del grafo"
        verbose_name_plural = "Aristas del grafo"
        ordering = ['origen', 'destino']
        unique_together = [['origen', 'destino']]

    def __str__(self):
        sentido = '↔' if self.bidireccional else '→'
        return f"{self.origen.nombre} {sentido} {self.destino.nombre} ({self.distancia_m}m)"

    def save(self, *args, **kwargs):
        # Calcular distancia automáticamente con fórmula de Haversine
        if not self.distancia_m or self.distancia_m == 0:
            self.distancia_m = self._calcular_distancia_haversine()
        super().save(*args, **kwargs)

    def _calcular_distancia_haversine(self):
        """Distancia en metros entre los 2 nodos (geográfica real)."""
        from math import radians, sin, cos, sqrt, atan2

        R = 6371000  # radio de la Tierra en metros
        lat1, lng1 = radians(float(self.origen.latitud)),  radians(float(self.origen.longitud))
        lat2, lng2 = radians(float(self.destino.latitud)), radians(float(self.destino.longitud))

        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return round(R * c, 2)