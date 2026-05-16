"""
locations/utils.py

Utilidades para la generación de imágenes QR.
"""

import io
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from django.core.files.base import ContentFile


def generar_imagen_qr(url_destino, color_primario=(14, 158, 142)):
    """
    Genera una imagen QR con estilo personalizado de CampusGo.

    Args:
        url_destino: La URL que se codifica dentro del QR.
        color_primario: Color RGB del QR (default: turquesa CampusGo #0E9E8E).

    Returns:
        ContentFile listo para asignarse a un ImageField.
    """
    qr = qrcode.QRCode(
        version=None,                          # auto-ajusta tamaño
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # 30% redundancia
        box_size=10,
        border=2,
    )
    qr.add_data(url_destino)
    qr.make(fit=True)

    # Imagen con módulos redondeados y color CampusGo
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=SolidFillColorMask(
            back_color=(255, 255, 255),
            front_color=color_primario
        ),
    )

    # Convertir la imagen a bytes para guardarla en el ImageField
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return ContentFile(buffer.getvalue())


def generar_qr_para_ubicacion(ubicacion, request=None, dominio_fallback="http://127.0.0.1:8000"):
    """
    Genera (o regenera) el QR asociado a una ubicación.

    Args:
        ubicacion: instancia de Ubicacion.
        request: HttpRequest opcional para construir URLs absolutas.
        dominio_fallback: si no hay request, usa este dominio.

    Returns:
        Instancia CodigoQR creada o actualizada.
    """
    from .models import CodigoQR

    # Construir la URL absoluta a donde apuntará el QR
    ruta = ubicacion.get_absolute_url()
    if request is not None:
        url_destino = request.build_absolute_uri(ruta)
    else:
        url_destino = f"{dominio_fallback}{ruta}"

    # Obtener o crear el código QR
    codigo_qr, _ = CodigoQR.objects.get_or_create(ubicacion=ubicacion)
    codigo_qr.url_destino = url_destino

    # Generar la nueva imagen
    imagen_qr = generar_imagen_qr(url_destino)
    nombre_archivo = f"{ubicacion.codigo}.png"
    codigo_qr.imagen.save(nombre_archivo, imagen_qr, save=False)
    codigo_qr.save()

    return codigo_qr
