"""
locations/admin.py

CAMBIO EN ESTA VERSIÓN:
  - CampusAdmin ahora tiene un botón "Editor de grafo" por cada campus
    que lleva a la pantalla visual con Leaflet
"""

from django.contrib import admin, messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html

from .models import Campus, Edificio, Ubicacion, CodigoQR, NodoGrafo, AristaGrafo
from .utils import generar_qr_para_ubicacion


# ============================================================
# CAMPUS
# ============================================================
@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'codigo', 'activo',
        'total_ubicaciones', 'total_nodos', 'total_aristas',
        'btn_editor_grafo',
    ]
    list_filter = ['activo']
    search_fields = ['nombre', 'codigo']
    prepopulated_fields = {'codigo': ('nombre',)}

    def total_ubicaciones(self, obj):
        return obj.ubicaciones.count()
    total_ubicaciones.short_description = "Ubicaciones"

    def total_nodos(self, obj):
        return obj.nodos.count()
    total_nodos.short_description = "Nodos"

    def total_aristas(self, obj):
        return AristaGrafo.objects.filter(origen__campus=obj).count()
    total_aristas.short_description = "Aristas"

    def btn_editor_grafo(self, obj):
        url = reverse('locations:admin_editor_grafo', args=[obj.codigo])
        return format_html(
            '<a class="button" href="{}" '
            'style="background:#0E9E8E; color:white; padding:6px 14px; '
            'border-radius:6px; text-decoration:none; font-size:12px; '
            'font-weight:700;">'
            '🗺️ Editor de grafo</a>', url
        )
    btn_editor_grafo.short_description = "Acciones"


# ============================================================
# EDIFICIO
# ============================================================
@admin.register(Edificio)
class EdificioAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'campus', 'pisos']
    list_filter = ['campus']
    search_fields = ['codigo', 'nombre']


# ============================================================
# UBICACIÓN
# ============================================================
@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'tipo', 'campus', 'edificio',
        'tiene_qr_badge', 'tiene_nodo_badge', 'acciones_qr', 'activo'
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
        }),
        ('Metadatos', {
            'fields': ('creado', 'actualizado'),
            'classes': ('collapse',)
        }),
    )

    actions = ['accion_generar_qrs']

    def accion_generar_qrs(self, request, queryset):
        creados = 0
        for ubicacion in queryset:
            generar_qr_para_ubicacion(ubicacion, request=request)
            creados += 1
        self.message_user(request, f"✅ Se generaron {creados} QR(s).", messages.SUCCESS)
    accion_generar_qrs.short_description = "🔄 Generar/regenerar QR de las seleccionadas"

    def tiene_qr_badge(self, obj):
        if obj.tiene_qr:
            return format_html('<span style="color: #0E9E8E; font-weight: bold;">✓ Sí</span>')
        return format_html('<span style="color: #888;">— No</span>')
    tiene_qr_badge.short_description = "QR"

    def tiene_nodo_badge(self, obj):
        if hasattr(obj, 'nodo_grafo') and obj.nodo_grafo:
            return format_html('<span style="color: #0E9E8E; font-weight: bold;">✓ Nodo</span>')
        return format_html('<span style="color: #888;">— Sin nodo</span>')
    tiene_nodo_badge.short_description = "Grafo"

    def acciones_qr(self, obj):
        url = reverse('admin:locations_ubicacion_generar_qr', args=[obj.pk])
        if obj.tiene_qr:
            return format_html(
                '<a class="button" href="{}" '
                'style="background:#E8721C; color:white; padding:4px 10px; '
                'border-radius:6px; text-decoration:none; font-size:12px;">'
                '🔄 Regenerar QR</a>', url
            )
        return format_html(
            '<a class="button" href="{}" '
            'style="background:#0E9E8E; color:white; padding:4px 10px; '
            'border-radius:6px; text-decoration:none; font-size:12px;">'
            '➕ Generar QR</a>', url
        )
    acciones_qr.short_description = "Acciones"

    def preview_qr(self, obj):
        if obj.pk and obj.tiene_qr and obj.codigo_qr.imagen:
            return format_html(
                '<div><img src="{}" style="width:200px; height:200px; '
                'border:1px solid #ddd; border-radius:8px;"/>'
                '<p style="margin-top:8px; font-size:12px; color:#666;">'
                'URL: <code>{}</code><br>Escaneos: <strong>{}</strong></p></div>',
                obj.codigo_qr.imagen.url, obj.codigo_qr.url_destino, obj.codigo_qr.escaneos
            )
        return format_html('<p style="color:#888;">Aún no se ha generado un QR.</p>')
    preview_qr.short_description = "Previsualización del QR"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:ubicacion_id>/generar-qr/',
                 self.admin_site.admin_view(self.vista_generar_qr),
                 name='locations_ubicacion_generar_qr'),
        ]
        return custom_urls + urls

    def vista_generar_qr(self, request, ubicacion_id):
        ubicacion = get_object_or_404(Ubicacion, pk=ubicacion_id)
        generar_qr_para_ubicacion(ubicacion, request=request)
        messages.success(request, f"✅ QR generado para «{ubicacion.nombre}».")
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
            return format_html('<img src="{}" style="width:50px; height:50px;"/>', obj.imagen.url)
        return "—"
    preview.short_description = "QR"

    def preview_grande(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" style="width:300px; height:300px; '
                'border:1px solid #ddd; border-radius:8px;"/>', obj.imagen.url
            )
        return "—"
    preview_grande.short_description = "Previsualización"


# ============================================================
# NODO DEL GRAFO
# ============================================================
@admin.register(NodoGrafo)
class NodoGrafoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'campus', 'ubicacion_vinculada', 'coords_display', 'activo']
    list_filter = ['campus', 'tipo', 'activo']
    search_fields = ['codigo', 'nombre']
    prepopulated_fields = {'codigo': ('nombre',)}
    autocomplete_fields = ['ubicacion']

    fieldsets = (
        ('Información', {
            'fields': ('campus', 'codigo', 'nombre', 'tipo', 'activo')
        }),
        ('Posición geográfica', {
            'fields': ('latitud', 'longitud'),
            'description': '💡 Para una experiencia más rápida usa el "Editor de grafo" '
                           'desde la lista de Campus: haz clic en el mapa y los nodos se crean solos.'
        }),
        ('Vinculación', {
            'fields': ('ubicacion',),
        }),
    )

    def ubicacion_vinculada(self, obj):
        if obj.ubicacion:
            return format_html(
                '<span style="color: #0E9E8E;">📌 {}</span>',
                obj.ubicacion.nombre
            )
        return format_html('<span style="color: #888;">—</span>')
    ubicacion_vinculada.short_description = "Vinculado a"

    def coords_display(self, obj):
        return format_html(
            '<code style="font-size: 11px;">{}, {}</code>',
            obj.latitud, obj.longitud
        )
    coords_display.short_description = "Coordenadas"


# ============================================================
# ARISTA DEL GRAFO
# ============================================================
@admin.register(AristaGrafo)
class AristaGrafoAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'tipo', 'distancia_m', 'accesible_badge', 'bidireccional', 'activo']
    list_filter = ['origen__campus', 'tipo', 'accesible', 'bidireccional', 'activo']
    search_fields = ['origen__nombre', 'destino__nombre']
    autocomplete_fields = ['origen', 'destino']
    readonly_fields = ['distancia_m', 'creado']

    fieldsets = (
        ('Conexión', {
            'fields': ('origen', 'destino', 'tipo', 'bidireccional')
        }),
        ('Características', {
            'fields': ('accesible', 'activo', 'distancia_m'),
            'description': 'La distancia se calcula automáticamente con Haversine.'
        }),
        ('Metadatos', {
            'fields': ('creado',),
            'classes': ('collapse',)
        }),
    )

    def accesible_badge(self, obj):
        if obj.accesible:
            return format_html('<span style="color: #0E9E8E;">✓ Sí</span>')
        return format_html('<span style="color: #E8721C;">⚠ No</span>')
    accesible_badge.short_description = "Accesible"