from django.db import models
from core.models import TimestampMixin, CreatedByMixin

class ThematicAxis(TimestampMixin, CreatedByMixin, models.Model):
    name = models.CharField(
        max_length=250, 
        unique=True,
        verbose_name="Nombre Eje Tematico"
    )

    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Descripcion"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )


    class Meta:
        db_table = 'thematic_axis'
        verbose_name = 'Eje Temático'
        verbose_name_plural = 'Ejes Temáticos'
        ordering = ['name']

    def __str__(self):
        return self.name