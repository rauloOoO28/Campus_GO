
# Register your models here.
"""
locations/admin.py

Configuración del admin de Django con:
  - Acción masiva para generar QRs
  - Botón individual "Generar QR" en cada ubicación
  - Previsualización del QR generado
"""

from django.contrib import admin, messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Campus, Edificio, Ubicacion, CodigoQR
from .utils import generar_qr_para_ubicacion


# ============================================================
# CAMPUS
# ============================================================
@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo', 'activo', 'total_ubicaciones']
    list_filter = ['activo']
    search_fields = ['nombre', 'codigo']
    prepopulated_fields = {'codigo': ('nombre',)}

    def total_ubicaciones(self, obj):
        return obj.ubicaciones.count()
    total_ubicaciones.short_description = "Ubicaciones"


# ============================================================
# EDIFICIO
# ============================================================
@admin.register(Edificio)
class EdificioAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'campus', 'pisos']
    list_filter = ['campus']
    search_fields = ['codigo', 'nombre']


# ============================================================
# UBICACIÓN (con botón Generar QR)
# ============================================================
@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'tipo', 'campus', 'edificio',
        'tiene_qr_badge', 'acciones_qr', 'activo'
    ]
    list_filter = ['campus', 'tipo', 'activo']
    search_fields = ['nombre', 'codigo', 'descripcion']
    prepopulated_fields = {'codigo': ('nombre',)}
    readonly_fields = ['creado', 'actualizado', 'preview_qr']

    fieldsets = (
        ('Información básica', {
            'fields': ('campus', 'edificio', 'tipo', 'codigo', 'nombre', 'descripcion')
        }),
        ('Ubicación geográfica', {
            'fields': ('latitud', 'longitud', 'piso')
        }),
        ('Información adicional', {
            'fields': ('capacidad', 'horario', 'activo')
        }),
        ('Código QR', {
            'fields': ('preview_qr',),
            'description': 'Usa el botón "Generar QR" en la lista de ubicaciones.'
        }),
        ('Metadatos', {
            'fields': ('creado', 'actualizado'),
            'classes': ('collapse',)
        }),
    )

    # Acciones masivas
    actions = ['accion_generar_qrs']

    def accion_generar_qrs(self, request, queryset):
        """Acción para generar QRs de varias ubicaciones a la vez."""
        creados = 0
        for ubicacion in queryset:
            generar_qr_para_ubicacion(ubicacion, request=request)
            creados += 1
        self.message_user(
            request,
            f"✅ Se generaron {creados} código(s) QR exitosamente.",
            messages.SUCCESS
        )
    accion_generar_qrs.short_description = "🔄 Generar/regenerar QR de las seleccionadas"

    # Badge en la lista
    def tiene_qr_badge(self, obj):
        if obj.tiene_qr:
            return format_html(
                '<span style="color: #0E9E8E; font-weight: bold;">✓ Sí</span>'
            )
        return format_html(
            '<span style="color: #888;">— No</span>'
        )
    tiene_qr_badge.short_description = "QR"

    # Botón "Generar QR" en cada fila
    def acciones_qr(self, obj):
        url = reverse('admin:locations_ubicacion_generar_qr', args=[obj.pk])
        if obj.tiene_qr:
            return format_html(
                '<a class="button" href="{}" '
                'style="background:#E8721C; color:white; padding:4px 10px; '
                'border-radius:6px; text-decoration:none; font-size:12px;">'
                '🔄 Regenerar QR</a>',
                url
            )
        return format_html(
            '<a class="button" href="{}" '
            'style="background:#0E9E8E; color:white; padding:4px 10px; '
            'border-radius:6px; text-decoration:none; font-size:12px;">'
            '➕ Generar QR</a>',
            url
        )
    acciones_qr.short_description = "Acciones"

    # Vista de previsualización dentro del formulario
    def preview_qr(self, obj):
        if obj.pk and obj.tiene_qr and obj.codigo_qr.imagen:
            return format_html(
                '<div>'
                '<img src="{}" style="width:200px; height:200px; '
                'border:1px solid #ddd; border-radius:8px;"/>'
                '<p style="margin-top:8px; font-size:12px; color:#666;">'
                'URL: <code>{}</code><br>'
                'Escaneos: <strong>{}</strong>'
                '</p></div>',
                obj.codigo_qr.imagen.url,
                obj.codigo_qr.url_destino,
                obj.codigo_qr.escaneos
            )
        return format_html(
            '<p style="color:#888;">'
            'Aún no se ha generado un QR. '
            'Guarda esta ubicación y usa el botón "Generar QR".'
            '</p>'
        )
    preview_qr.short_description = "Previsualización del QR"

    # URLs extra para el botón
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:ubicacion_id>/generar-qr/',
                self.admin_site.admin_view(self.vista_generar_qr),
                name='locations_ubicacion_generar_qr',
            ),
        ]
        return custom_urls + urls

    def vista_generar_qr(self, request, ubicacion_id):
        """Vista que se dispara al hacer clic en el botón "Generar QR"."""
        ubicacion = get_object_or_404(Ubicacion, pk=ubicacion_id)
        generar_qr_para_ubicacion(ubicacion, request=request)
        messages.success(
            request,
            f"✅ QR generado correctamente para «{ubicacion.nombre}»."
        )
        return redirect('admin:locations_ubicacion_changelist')


# ============================================================
# CÓDIGO QR
# ============================================================
@admin.register(CodigoQR)
class CodigoQRAdmin(admin.ModelAdmin):
    list_display = ['ubicacion', 'escaneos', 'ultimo_escaneo', 'preview', 'creado']
    list_filter = ['creado']
    readonly_fields = ['url_destino', 'escaneos', 'ultimo_escaneo', 'creado', 'preview_grande']
    search_fields = ['ubicacion__nombre', 'ubicacion__codigo']

    def preview(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="width:50px; height:50px;"/>',
                obj.imagen.url
            )
        return "—"
    preview.short_description = "QR"

    def preview_grande(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="width:300px; height:300px; '
                'border:1px solid #ddd; border-radius:8px;"/>',
                obj.imagen.url
            )
        return "—"
    preview_grande.short_description = "Previsualización"
