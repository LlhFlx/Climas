from django.db import models
from core.models import TimestampMixin, CreatedByMixin
from expressions.models import Expression
from strategic_effects.models import StrategicEffect

class Product(TimestampMixin, CreatedByMixin, models.Model):
    """
    Producto derivado de una Expresión de Interés.
    Puede estar asociado a múltiples efectos estratégicos.
    """
    expression = models.ForeignKey(
        'expressions.Expression',
        on_delete=models.CASCADE,
        verbose_name="Expresion de Interes"
    )

    title = models.CharField(
        max_length=200,
        verbose_name="Titulo del Producto"
    )

    description = models.TextField(
        verbose_name="Descripcion"
    )

    outcome = models.TextField(verbose_name="Resultado o impacto.")

    start_date = models.DateField(verbose_name="Fecha de Inicio")

    end_date = models.DateField(verbose_name="Fecha de Finalizacion")

    strategic_effects = models.ManyToManyField(
        'strategic_effects.StrategicEffect',
        related_name='products',
        blank=True,
        verbose_name="Efectos Estrategicos"
    )
 
    status = models.ForeignKey(
        'common.Status',
        on_delete=models.PROTECT,
        verbose_name="Estado"
    )

    class Meta:
        db_table = 'product'
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-created_at']

    def __str__(self):
        return self.title
