from django.db import models
from django.contrib.auth.models import User


class Perfil(models.Model):
    ROL_CHOICES = [
        ("alumno", "Alumno"),
        ("visitante", "Visitante"),
        ("maestro", "Maestro"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    nombre_completo = models.CharField(max_length=200)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_completo} ({self.get_rol_display()})"
