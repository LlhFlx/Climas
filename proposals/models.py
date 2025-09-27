from django.db import models

from expressions.models import Expression 

class Proposal(Expression):
    """
    Propuesta formal — expresión aprobada con campos adicionales.
    Hereda todos los campos de Expression, más los nuevos.
    """
    # NEW FIELDS specific to Proposal
    budget_breakdown = models.TextField(
        verbose_name="Desglose Presupuestario",
        help_text="Detalles de asignación de fondos por actividad"
    )
    implementation_plan = models.TextField(
        verbose_name="Plan de Implementación",
        help_text="Fases, cronograma, hitos"
    )
    risk_analysis = models.TextField(
        verbose_name="Análisis de Riesgos",
        help_text="Riesgos identificados y planes de mitigación"
    )
    sustainability_plan = models.TextField(
        verbose_name="Plan de Sostenibilidad",
        help_text="Cómo se mantendrá el proyecto después del financiamiento"
    )

    # Override field from Expression if needed
    scale = models.ForeignKey(
        'common.Scale',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Escala del Presupuesto",
        help_text="Escalado revisado para propuesta"
    )

    class Meta:
        verbose_name = "Propuesta"
        verbose_name_plural = "Propuestas"
        db_table = 'proposal'

    def __str__(self):
        return f"PROPUESTA: {self.project_title}"