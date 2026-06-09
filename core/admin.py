from django.contrib import admin
from .models import Favorito, Historial


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ('user', 'campus', 'creado')
    search_fields = ('user__username', 'campus__nombre', 'campus__codigo')
    list_filter = ('creado',)


@admin.register(Historial)
class HistorialAdmin(admin.ModelAdmin):
    list_display = ('user', 'campus', 'visitado_el')
    search_fields = ('user__username', 'campus__nombre', 'campus__codigo')
    list_filter = ('visitado_el',)
