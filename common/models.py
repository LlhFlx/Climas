from django.db import models
from core.models import TimestampMixin

class Status(TimestampMixin, models.Model):
    """
    Status generico para entidades como Convocatorias, 
    Propuestas y Evaluaciones
    """
    name = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name='Nombre'
    )
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Descripcion'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    color = models.CharField(
        max_length=20, 
        blank=True,
        help_text=""
    )

    class Meta:
        db_table = 'common_status'
        verbose_name = 'Estado'
        verbose_name_plural = "Estados"

    def __str__(self):
        return self.name