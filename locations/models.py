"""
locations/models.py

Modelos para gestionar campus, edificios y ubicaciones de CampusGo.
Por ahora solo trabajamos con ESCOM-IPN.
"""

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


# ============================================================
# CAMPUS
# ============================================================
class Campus(models.Model):
    codigo = models.SlugField(
        max_length=50, unique=True,
        help_text="Identificador único en URLs (ej. 'escom-ipn')"
    )
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
    campus = models.ForeignKey(
        Campus, on_delete=models.CASCADE, related_name='edificios'
    )
    codigo = models.CharField(
        max_length=10,
        help_text="Código corto del edificio (ej. 'A', '1', 'H')"
    )
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    pisos = models.PositiveSmallIntegerField(default=1)

    latitud = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Latitud geográfica del edificio (ej. 19.504505)"
    )
    longitud = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Longitud geográfica del edificio (ej. -99.146911)"
    )

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
    TIPO_ENTRADA = 'entrada'
    TIPO_AULA = 'aula'
    TIPO_LABORATORIO = 'laboratorio'
    TIPO_OFICINA = 'oficina'
    TIPO_SERVICIO = 'servicio'

    TIPOS = [
        (TIPO_ENTRADA, 'Entrada'),
        (TIPO_AULA, 'Aula'),
        (TIPO_LABORATORIO, 'Laboratorio'),
        (TIPO_OFICINA, 'Oficina'),
        (TIPO_SERVICIO, 'Servicio (cafetería, biblioteca, etc.)'),
    ]

    campus = models.ForeignKey(
        Campus, on_delete=models.CASCADE, related_name='ubicaciones'
    )
    # Edificio puede ser null (caso de entradas exteriores que no
    # pertenecen a ningún edificio)
    edificio = models.ForeignKey(
        Edificio, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ubicaciones'
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    codigo = models.SlugField(
        max_length=80, unique=True,
        help_text="Identificador único usado en URLs y QRs (ej. 'escom-entrada-principal')"
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)

    # Coordenadas geográficas
    latitud = models.DecimalField(max_digits=10, decimal_places=7)
    longitud = models.DecimalField(max_digits=10, decimal_places=7)

    # Información adicional
    piso = models.IntegerField(
        default=0,
        help_text="0 para planta baja o exterior"
    )
    capacidad = models.PositiveIntegerField(null=True, blank=True)
    horario = models.CharField(
        max_length=200, blank=True,
        help_text="Ej. 'L-V 7:00-21:00 · S 8:00-14:00'"
    )

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
        # Auto-generar el slug si está vacío
        if not self.codigo:
            base = f"{self.campus.codigo}-{self.tipo}-{self.nombre}"
            self.codigo = slugify(base)[:80]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """URL del detalle de esta ubicación (a donde apunta el QR)."""
        return reverse('locations:detalle_publico', kwargs={'codigo': self.codigo})

    @property
    def tiene_qr(self):
        return hasattr(self, 'codigo_qr')


# ============================================= ===============
# CÓDIGO QR
# ============================================================
def qr_upload_path(instance, filename):
    """Guarda el QR como qrs/<codigo-ubicacion>.png"""
    return f"qrs/{instance.ubicacion.codigo}.png"


class CodigoQR(models.Model):
    ubicacion = models.OneToOneField(
        Ubicacion, on_delete=models.CASCADE, related_name='codigo_qr'
    )
    imagen = models.ImageField(upload_to=qr_upload_path, blank=True)
    url_destino = models.URLField(
        max_length=500,
        help_text="URL que se codifica dentro del QR"
    )
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
        """Llamar cada vez que alguien escanea el QR."""
        from django.utils import timezone
        self.escaneos += 1
        self.ultimo_escaneo = timezone.now()
        self.save(update_fields=['escaneos', 'ultimo_escaneo'])
