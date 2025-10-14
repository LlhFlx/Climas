from django.db import models
from core.models import TimestampMixin, CreatedByMixin
from expressions.models import Expression
from strategic_effects.models import StrategicEffect


class BaseProduct(TimestampMixin, CreatedByMixin, models.Model):
    """
    Clase base para Productos (Expression o Proposal).
    """
    title = models.CharField(
        max_length=200,
        verbose_name="Titulo del Producto"
    )

    description = models.TextField(
        verbose_name="Descripcion"
    )

    outcome = models.TextField(
        verbose_name="Resultado o impacto."
    )

    start_date = models.DateField(
        verbose_name="Fecha de Inicio",
        blank=True,
        null=True
    )

    end_date = models.DateField(
        verbose_name="Fecha de Finalizacion",
        blank=True,
        null=True
    )

    strategic_effects = models.ManyToManyField(
        'strategic_effects.StrategicEffect',
        related_name="%(class)s_products",  # dynamic related name per subclass
        blank=True,
        verbose_name="Efectos Estrategicos"
    )

    status = models.ForeignKey(
        'common.Status',
        on_delete=models.PROTECT,
        verbose_name="Estado"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
class ExpressionProduct(BaseProduct):
    """
    Producto derivado de una Expresión de Interés.
    Puede estar asociado a múltiples efectos estratégicos.
    """
    expression = models.ForeignKey(
        'expressions.Expression',
        on_delete=models.CASCADE,
        verbose_name="Expresion de Interes"
    )

    class Meta:
        db_table = 'expression_product'
        verbose_name = "Producto de Expresión"
        verbose_name_plural = "Productos de Expresión"

class ProposalProduct(BaseProduct):
    """
    Producto derivado de una Propuesta.
    """
    proposal = models.ForeignKey(
        'proposals.Proposal',
        on_delete=models.CASCADE,
        verbose_name="Propuesta"
    )

    class Meta:
        db_table = 'proposal_product'
        verbose_name = "Producto de Propuesta"
        verbose_name_plural = "Productos de Propuesta"