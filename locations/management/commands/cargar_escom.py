"""
locations/management/commands/cargar_escom.py

Comando para precargar datos básicos de ESCOM-IPN.
Crea el campus + 2 entradas principales.

Uso:
    python manage.py cargar_escom
    python manage.py cargar_escom --con-qr   # también genera los QR

Nota: Las coordenadas son aproximadas, ajústalas con valores reales
      tomados con Google Maps (clic derecho → "¿Qué hay aquí?").
"""

from django.core.management.base import BaseCommand
from locations.models import Campus, Ubicacion
from locations.utils import generar_qr_para_ubicacion


# Datos de ESCOM-IPN
DATOS_CAMPUS = {
    'codigo': 'escom-ipn',
    'nombre': 'ESCOM IPN',
    'direccion': 'Av. Juan de Dios Bátiz s/n esq. Miguel Othón de Mendizábal, '
                 'Col. Lindavista, Gustavo A. Madero, CDMX',
    'descripcion': 'Escuela Superior de Cómputo del Instituto Politécnico Nacional. '
                   'Campus Unidad Profesional Adolfo López Mateos (Zacatenco).',
}

ENTRADAS = [
    {
        'codigo': 'escom-entrada-principal',
        'nombre': 'Entrada Principal ESCOM',
        'descripcion': 'Acceso principal a la ESCOM desde Av. Juan de Dios Bátiz. '
                       'Cuenta con caseta de vigilancia y control de acceso.',
        'latitud':  19.5043270,
        'longitud': -99.1466870,
        'horario': 'L-V 6:00-22:00 · S 7:00-15:00',
    },
    {
        'codigo': 'escom-entrada-posterior',
        'nombre': 'Entrada Posterior (Wilfrido Massieu)',
        'descripcion': 'Acceso peatonal alternativo desde Av. Wilfrido Massieu. '
                       'Útil para llegar a edificios del lado norte del campus.',
        'latitud':  19.5057000,
        'longitud': -99.1471000,
        'horario': 'L-V 7:00-20:00',
    },
]


class Command(BaseCommand):
    help = "Precarga el campus ESCOM-IPN con 2 entradas principales."

    def add_arguments(self, parser):
        parser.add_argument(
            '--con-qr',
            action='store_true',
            help='Genera también los códigos QR de cada entrada.',
        )
        parser.add_argument(
            '--dominio',
            type=str,
            default='http://127.0.0.1:8000',
            help='Dominio base que se incluirá en los QR (default: localhost).',
        )

    def handle(self, *args, **opts):
        con_qr = opts['con_qr']
        dominio = opts['dominio']

        # 1. Crear/obtener el campus
        campus, creado_campus = Campus.objects.get_or_create(
            codigo=DATOS_CAMPUS['codigo'],
            defaults={
                'nombre': DATOS_CAMPUS['nombre'],
                'direccion': DATOS_CAMPUS['direccion'],
                'descripcion': DATOS_CAMPUS['descripcion'],
                'activo': True,
            },
        )
        if creado_campus:
            self.stdout.write(self.style.SUCCESS(f"✅ Campus creado: {campus.nombre}"))
        else:
            self.stdout.write(self.style.WARNING(f"ℹ️  Campus ya existía: {campus.nombre}"))

        # 2. Crear las entradas
        creadas = 0
        existentes = 0
        for entrada in ENTRADAS:
            ubicacion, creada = Ubicacion.objects.get_or_create(
                codigo=entrada['codigo'],
                defaults={
                    'campus':      campus,
                    'tipo':        Ubicacion.TIPO_ENTRADA,
                    'nombre':      entrada['nombre'],
                    'descripcion': entrada['descripcion'],
                    'latitud':     entrada['latitud'],
                    'longitud':    entrada['longitud'],
                    'horario':     entrada['horario'],
                    'activo':      True,
                },
            )
            if creada:
                creadas += 1
                self.stdout.write(self.style.SUCCESS(f"  ✅ {ubicacion.nombre}"))
            else:
                existentes += 1
                self.stdout.write(self.style.WARNING(f"  ℹ️  {ubicacion.nombre} ya existía"))

            # 3. Generar QR si se solicitó
            if con_qr:
                generar_qr_para_ubicacion(ubicacion, dominio_fallback=dominio)
                self.stdout.write(f"     🔄 QR generado → {dominio}{ubicacion.get_absolute_url()}")

        # Resumen
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Resumen:\n"
            f"  • Campus:       {campus.nombre}\n"
            f"  • Entradas nuevas:    {creadas}\n"
            f"  • Entradas existentes: {existentes}\n"
            f"  • QR generados:        {'sí' if con_qr else 'no (usa --con-qr)'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ))
