from django.db import models
from core.models import TimestampMixin

class IntersectionalityScope(TimestampMixin, models.Model):
    """
    Ámbito de interseccionalidad (ej: Género, Juventud, Pueblos Indígenas).
    Usado para marcar expresiones que abordan dimensiones sociales específicas.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descripción"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    class Meta:
        db_table = 'intersectionality_scope'
        verbose_name = "Ámbito de Interseccionalidad"
        verbose_name_plural = "Ámbitos de Interseccionalidad"
        ordering = ['name']

    def __str__(self):
        return self.name