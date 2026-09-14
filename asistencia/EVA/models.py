from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .validators import validar_documento


class Usuario(AbstractUser):

    ROLES = [
        ("estudiante", "Estudiante"),
        ("validador", "Validador"),
        ("receptor", "Receptor"),
    ]

    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default="estudiante"
    )

    rut = models.CharField(
        max_length=12,
        unique=True,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.username} ({self.get_rol_display()})"


class Asistencia(models.Model):

    ESTADOS = [
        ("Presente", "Presente"),
        ("Ausente", "Ausente"),
        ("Justificado", "Justificado"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="asistencias"
    )

    fecha = models.DateField(
        default=timezone.localdate
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="Presente"
    )

    class Meta:
        ordering = ["-fecha"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "fecha"],
                name="unique_asistencia_usuario_fecha"
            )
        ]

    def __str__(self):
        return (
            f"{self.usuario.username} - "
            f"{self.fecha.strftime('%d/%m/%Y')} - "
            f"{self.estado}"
        )


class Justificacion(models.Model):

    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("aprobada", "Aprobada"),
        ("rechazada", "Rechazada"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="justificaciones"
    )

    fecha_inasistencia = models.DateField()

    motivo = models.CharField(
        max_length=200
    )

    descripcion = models.TextField(
        blank=True,
        null=True
    )

    documento = models.FileField(
        upload_to="justificaciones/",
        blank=True,
        null=True,
        validators=[validar_documento]
    )

    estado = models.CharField(
        max_length=10,
        choices=ESTADOS,
        default="pendiente"
    )

    comentarios_validador = models.TextField(
        blank=True,
        null=True
    )

    fecha_envio = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-fecha_envio"]

    def __str__(self):
        return (
            f"{self.usuario.username} - "
            f"{self.fecha_inasistencia} - "
            f"{self.get_estado_display()}"
        )