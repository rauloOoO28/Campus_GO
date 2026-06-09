"""
locations/management/commands/cargar_grafo_escom.py

Precarga el grafo de rutas de ESCOM (10 nodos + 12 aristas) en 1 paso.

Uso:
    python manage.py cargar_grafo_escom              # Solo crea si no existe
    python manage.py cargar_grafo_escom --reset      # Borra grafo previo y recrea

MEJORA: ahora detecta conflictos (nodos previos vinculados a las mismas
ubicaciones) y avisa con un mensaje claro en lugar de fallar.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from locations.models import Campus, Ubicacion, NodoGrafo, AristaGrafo


# Nodos propuestos para ESCOM
NODOS_BASE = [
    {
        'codigo':   'escom-entrada-principal-nodo',
        'nombre':   'Entrada Principal',
        'tipo':     NodoGrafo.TIPO_ENTRADA,
        'lat':      19.5043270,
        'lng':     -99.1466870,
        'vincular_a': 'escom-entrada-principal',
    },
    {
        'codigo':   'escom-entrada-posterior-nodo',
        'nombre':   'Entrada Posterior',
        'tipo':     NodoGrafo.TIPO_ENTRADA,
        'lat':      19.5057000,
        'lng':     -99.1471000,
        'vincular_a': 'escom-entrada-posterior',
    },
    {
        'codigo':   'escom-explanada-central',
        'nombre':   'Explanada Central',
        'tipo':     NodoGrafo.TIPO_PLAZA,
        'lat':      19.5048500,
        'lng':     -99.1467000,
    },
    {
        'codigo':   'escom-cruce-edif-1-2',
        'nombre':   'Cruce Edif. 1 - 2',
        'tipo':     NodoGrafo.TIPO_CRUCE,
        'lat':      19.5049500,
        'lng':     -99.1464500,
    },
    {
        'codigo':   'escom-cruce-edif-3-4',
        'nombre':   'Cruce Edif. 3 - 4',
        'tipo':     NodoGrafo.TIPO_CRUCE,
        'lat':      19.5051000,
        'lng':     -99.1466000,
    },
    {
        'codigo':   'escom-frente-edif-1',
        'nombre':   'Frente Edif. 1',
        'tipo':     NodoGrafo.TIPO_EDIFICIO,
        'lat':      19.5049000,
        'lng':     -99.1462500,
    },
    {
        'codigo':   'escom-frente-edif-2',
        'nombre':   'Frente Edif. 2',
        'tipo':     NodoGrafo.TIPO_EDIFICIO,
        'lat':      19.5050500,
        'lng':     -99.1464500,
    },
    {
        'codigo':   'escom-frente-edif-3',
        'nombre':   'Frente Edif. 3',
        'tipo':     NodoGrafo.TIPO_EDIFICIO,
        'lat':      19.5052000,
        'lng':     -99.1465000,
    },
    {
        'codigo':   'escom-frente-edif-4',
        'nombre':   'Frente Edif. 4',
        'tipo':     NodoGrafo.TIPO_EDIFICIO,
        'lat':      19.5053500,
        'lng':     -99.1467000,
    },
    {
        'codigo':   'escom-frente-gobierno',
        'nombre':   'Frente Edif. Gobierno',
        'tipo':     NodoGrafo.TIPO_EDIFICIO,
        'lat':      19.5047000,
        'lng':     -99.1469000,
    },
]


ARISTAS_BASE = [
    ('escom-entrada-principal-nodo', 'escom-explanada-central'),
    ('escom-explanada-central',      'escom-cruce-edif-1-2'),
    ('escom-explanada-central',      'escom-cruce-edif-3-4'),
    ('escom-explanada-central',      'escom-frente-gobierno'),
    ('escom-cruce-edif-1-2',         'escom-frente-edif-1'),
    ('escom-cruce-edif-1-2',         'escom-frente-edif-2'),
    ('escom-cruce-edif-3-4',         'escom-frente-edif-3'),
    ('escom-cruce-edif-3-4',         'escom-frente-edif-4'),
    ('escom-frente-edif-4',          'escom-entrada-posterior-nodo'),
    ('escom-cruce-edif-3-4',         'escom-entrada-posterior-nodo'),
    ('escom-frente-edif-2',          'escom-frente-edif-3'),
    ('escom-cruce-edif-1-2',         'escom-cruce-edif-3-4'),
]


class Command(BaseCommand):
    help = "Precarga el grafo de rutas de ESCOM (10 nodos + 12 aristas)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Borra el grafo existente antes de crearlo.',
        )

    def handle(self, *args, **opts):
        try:
            campus = Campus.objects.get(codigo='escom-ipn')
        except Campus.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                "❌ No existe el campus 'escom-ipn'. "
                "Corre antes: python manage.py cargar_escom"
            ))
            return

        # ============================================================
        # RESET si se pidió
        # ============================================================
        if opts['reset']:
            with transaction.atomic():
                n_aristas = AristaGrafo.objects.filter(origen__campus=campus).count()
                n_nodos = campus.nodos.count()
                AristaGrafo.objects.filter(origen__campus=campus).delete()
                campus.nodos.all().delete()
            self.stdout.write(self.style.WARNING(
                f"🗑️  Grafo previo borrado: {n_nodos} nodos y {n_aristas} aristas\n"
            ))

        # ============================================================
        # ⭐ DETECCIÓN DE CONFLICTOS (antes de empezar a crear)
        # ============================================================
        # Verificamos si las ubicaciones que queremos vincular ya tienen otro nodo
        conflictos = []
        for nodo_data in NODOS_BASE:
            vincular_a = nodo_data.get('vincular_a')
            if not vincular_a:
                continue

            try:
                ubicacion = Ubicacion.objects.get(codigo=vincular_a, campus=campus)
            except Ubicacion.DoesNotExist:
                continue

            # ¿Esta ubicación ya tiene un nodo asociado?
            if hasattr(ubicacion, 'nodo_grafo') and ubicacion.nodo_grafo:
                nodo_existente = ubicacion.nodo_grafo
                # Si NO es el mismo nodo que queremos crear, es un conflicto
                if nodo_existente.codigo != nodo_data['codigo']:
                    conflictos.append({
                        'ubicacion': ubicacion.nombre,
                        'nodo_existente': nodo_existente.nombre,
                        'nodo_existente_codigo': nodo_existente.codigo,
                    })

        if conflictos:
            self.stderr.write(self.style.ERROR(
                "\n❌ CONFLICTO DETECTADO\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Las siguientes ubicaciones YA tienen un nodo vinculado:\n"
            ))
            for c in conflictos:
                self.stderr.write(self.style.ERROR(
                    f"  • Ubicación «{c['ubicacion']}»\n"
                    f"    └─ ya está vinculada al nodo «{c['nodo_existente']}» "
                    f"(código: {c['nodo_existente_codigo']})"
                ))

            self.stderr.write(self.style.WARNING(
                "\n💡 SOLUCIONES POSIBLES:\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "  A) Borra el grafo previo y vuelve a correr (recomendado):\n"
                "     python manage.py cargar_grafo_escom --reset\n\n"
                "  B) Borra manualmente los nodos en conflicto desde el admin:\n"
                "     http://127.0.0.1:8000/admin/locations/nodografo/\n"
            ))
            return

        # ============================================================
        # CREAR NODOS
        # ============================================================
        nodos_creados = {}
        nodos_nuevos = 0
        nodos_existentes = 0

        for nodo_data in NODOS_BASE:
            ubicacion = None
            vincular_a = nodo_data.get('vincular_a')
            if vincular_a:
                try:
                    ubicacion = Ubicacion.objects.get(codigo=vincular_a, campus=campus)
                except Ubicacion.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"   ⚠️  No se encontró la ubicación '{vincular_a}' para vincular"
                    ))

            nodo, creado = NodoGrafo.objects.get_or_create(
                codigo=nodo_data['codigo'],
                defaults={
                    'campus':   campus,
                    'nombre':   nodo_data['nombre'],
                    'tipo':     nodo_data['tipo'],
                    'latitud':  nodo_data['lat'],
                    'longitud': nodo_data['lng'],
                    'ubicacion': ubicacion,
                },
            )

            nodos_creados[nodo_data['codigo']] = nodo

            if creado:
                nodos_nuevos += 1
                vinc = f" → vinculado a «{ubicacion.nombre}»" if ubicacion else ""
                self.stdout.write(self.style.SUCCESS(
                    f"  ✅ Nodo: {nodo.nombre}{vinc}"
                ))
            else:
                nodos_existentes += 1
                self.stdout.write(self.style.WARNING(
                    f"  ℹ️  Nodo ya existía: {nodo.nombre}"
                ))

        # ============================================================
        # CREAR ARISTAS
        # ============================================================
        aristas_nuevas = 0
        aristas_existentes = 0

        for origen_cod, destino_cod in ARISTAS_BASE:
            origen = nodos_creados.get(origen_cod)
            destino = nodos_creados.get(destino_cod)

            if not origen or not destino:
                self.stdout.write(self.style.WARNING(
                    f"  ⚠️  No se pudo crear arista {origen_cod} ↔ {destino_cod} "
                    f"(falta uno de los nodos)"
                ))
                continue

            existente = AristaGrafo.objects.filter(
                origen__in=[origen, destino],
                destino__in=[origen, destino],
            ).first()

            if existente:
                aristas_existentes += 1
                continue

            arista = AristaGrafo.objects.create(
                origen=origen,
                destino=destino,
                tipo=AristaGrafo.TIPO_SENDERO,
                accesible=True,
                bidireccional=True,
            )
            aristas_nuevas += 1
            self.stdout.write(self.style.SUCCESS(
                f"  🔗 Arista: {origen.nombre} ↔ {destino.nombre} ({arista.distancia_m}m)"
            ))

        # ============================================================
        # RESUMEN
        # ============================================================
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Resumen:\n"
            f"  • Nodos nuevos:        {nodos_nuevos}\n"
            f"  • Nodos ya existían:   {nodos_existentes}\n"
            f"  • Aristas nuevas:      {aristas_nuevas}\n"
            f"  • Aristas ya existían: {aristas_existentes}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ))
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"🎯 Listo. Abre el editor visual para ajustar posiciones:\n"
            f"   http://127.0.0.1:8000/grafo/escom-ipn/\n"
        ))