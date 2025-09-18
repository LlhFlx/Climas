from django.db import models
from core.models import TimestampMixin, CreatedByMixin
from expressions.models import Expression
from django.core.validators import MinValueValidator

class BudgetCategory(TimestampMixin, CreatedByMixin, models.Model):
    """
    Categoria de presupuesto (ej: 'Personal', 'Equipos', 'Viajes').
    Cargada via fixture, inmutable.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Descripcion"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )

    class Meta:
        db_table = 'budget_category'
        verbose_name = "Categoria de Presupuesto"
        verbose_name_plural = "Categorias de Presupuesto"
        ordering = ['name']

    def __str__(self):
        return self.name

class BudgetPeriod(TimestampMixin, CreatedByMixin, models.Model):
    """
    Periodo de presupuesto (Ej: Year 1 - Primer Semestre).
    Cargado via fixture, inmutable.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre"
    )

    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        db_table = 'budget_period'
        verbose_name = "Período de Presupuesto"
        verbose_name_plural = "Períodos de Presupuesto"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

class BudgetItem(TimestampMixin, models.Model):
    """
    Ítem de presupuesto para una expresión.
    Relaciona categoría, período y monto.
    """
    expression = models.ForeignKey(
        'expressions.Expression',
        on_delete=models.CASCADE,
        verbose_name="Expresión de Interés"
    )
    category = models.ForeignKey(
        'budgets.BudgetCategory',
        on_delete=models.PROTECT,
        verbose_name="Categoría"
    )
    period = models.ForeignKey(
        'budgets.BudgetPeriod',
        on_delete=models.PROTECT,
        verbose_name="Período"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Monto"
    )
    notes = models.TextField(blank=True, verbose_name="Notas")

    class Meta:
        db_table = 'budget_item'
        verbose_name = "Ítem de Presupuesto"
        verbose_name_plural = "Ítems de Presupuesto"
        unique_together = ('expression', 'category', 'period')
        ordering = ['category__name', 'period__order']

    def __str__(self):
        return f"{self.expression.project_title} - {self.category.name} ({self.period.name})"