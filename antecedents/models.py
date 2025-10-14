from django.db import models
from core.models import TimestampMixin
from institutions.models import Institution


class ProjectAntecedent(TimestampMixin, models.Model):
    """
    Proyecto anterior (antecedente) en el que una o más instituciones han participado.
    Usado para demostrar experiencia institucional en nuevas propuestas.
    """
    title = models.CharField(max_length=200, verbose_name="Título del Proyecto")
    description = models.TextField(verbose_name="Descripción")
    start_date = models.DateField(verbose_name="Fecha de Inicio")
    end_date = models.DateField(verbose_name="Fecha de Finalización")
    funding_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Monto Financiado"
    )
    funding_source = models.CharField(
        max_length=100,
        verbose_name="Fuente de Financiamiento"
    )
    outcomes = models.TextField(verbose_name="Resultados o Impactos")
    url = models.URLField(blank=True, verbose_name="URL de Evidencia")

    # Many-to-Many: Institutions that participated
    institutions = models.ManyToManyField(
        'institutions.Institution',
        related_name='project_antecedents',
        verbose_name="Instituciones Participantes"
    )

    class Meta:
        db_table = 'project_antecedent'
        verbose_name = "Proyecto Antecedente"
        verbose_name_plural = "Proyectos Antecedentes"
        ordering = ['-end_date', 'title']

    def __str__(self):
        return self.title