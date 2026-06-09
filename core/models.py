from django.db import models
from django.contrib.auth.models import User
from locations.models import Campus


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


class Favorito(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoritos')
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='favoritos')
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['user', 'campus']]
        ordering = ['-creado']

    def __str__(self):
        return f"{self.user.username} · {self.campus.nombre}"


class Historial(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='historial')
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='historial')
    visitado_el = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-visitado_el']

    def __str__(self):
        return f"{self.user.username} · {self.campus.nombre} @ {self.visitado_el.isoformat()}"
