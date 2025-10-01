from django.db import models

from django.contrib.contenttypes.fields import GenericRelation
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

    evaluations = GenericRelation(
        'evaluations.Evaluation',
        content_type_field='target_content_type',
        object_id_field='target_object_id',
        related_query_name='proposal'
    )

    class Meta:
        verbose_name = "Propuesta"
        verbose_name_plural = "Propuestas"
        db_table = 'proposal'

    def __str__(self):
        return f"PROPUESTA: {self.project_title}"