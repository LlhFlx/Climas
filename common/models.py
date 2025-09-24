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
    
class Scale(TimestampMixin, models.Model):
    """
    Budget scale categories for Expression.
    Used to classify project size based on total budget.
    """
    name = models.CharField(
        max_length=1,
        unique=True,
        choices=[('S', 'Pequeña'), ('M', 'Mediana'), ('B', 'Grande')],
        verbose_name="Escala"
    )
    description = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Descripción"
    )
    min_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Monto Mínimo (COP)"
    )
    max_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto Máximo (COP)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        db_table = 'scale'
        verbose_name = "Escala de Presupuesto"
        verbose_name_plural = "Escala de Presupuesto"
        ordering = ['min_amount']

    def __str__(self):
        return f"{self.name} - {self.description}"

    def save(self, *args, **kwargs):
        if not self.description:
            self.description = self.get_name_display()
        super().save(*args, **kwargs)