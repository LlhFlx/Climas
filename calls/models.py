from django.db import models
from core.models import TimestampMixin, CreatedByMixin
from django.core.validators import RegexValidator

class Call(TimestampMixin, CreatedByMixin, models.Model):
    id = models.AutoField(
        primary_key=True,
        verbose_name="ID Convocatoria"
    )

    coordinator = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL, # We keep the call entry even  if the user is deleted
        null=True,
        blank=True,
        related_name='coordinated_calls',
        db_index=True,
        verbose_name="Coordinador",
        help_text="Usuario responsable de gestionar esta convocatoria"
    )

    status = models.ForeignKey(
        'common.Status',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calls',
        db_index=True,
        verbose_name="Estado",
        help_text="Estado actual de la convocatoria (ej. Abierta, Cerrada)"
    )

    title = models.CharField(
        unique=True,
        verbose_name="Titulo",
        max_length=255
    )
    description = models.TextField(
        verbose_name="Descripcion"
    )
    opening_datetime = models.DateTimeField(
        db_index=True,
        verbose_name="Fecha de Apertura"
    )
    closing_datetime = models.DateTimeField(
        db_index=True,
        verbose_name="Fecha de Cierre"
    )

    class Meta:
        db_table= 'calls'
        verbose_name = 'Convocatoria'
        verbose_name_plural = 'Convocatorias'
        ordering = ['-opening_datetime'] # Newest first
        
    def __str__(self):
        return self.title
    
    # Method called before saving a model instance
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.opening_datetime and self.closing_datetime:
            if self.opening_datetime >= self.closing_datetime:
                raise ValidationError('La fecha de apertura debe ser anterior a la fecha de cierre.')
            
    def save(self, *args, **kwargs):
        # Always validate
        self.clean()
        super().save(*args, **kwargs)