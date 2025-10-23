from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from expressions.models import Expression
from common.models import Status
from geo.models import Country
from django.core.validators import MinValueValidator
from django.utils import timezone
from core.models import TimestampMixin
import os
from uuid import uuid4
from django.utils.text import get_valid_filename
from django.utils import timezone
from common.models import Status

def proposal_file_upload_path(instance, filename):
    """
    Custom upload path: /proposal_documents/{timeline|budget|commitment}/{year}/{month}/{day}/<uuid>-<filename>
    Ensures unique filenames, safe names, and organized storage.
    """
    ext = os.path.splitext(filename)[1]  # Get extension (.pdf, .docx, etc.)
    safe_name = get_valid_filename(filename)  # Sanitize filename
    new_filename = f"{uuid4().hex[:8]}-{safe_name}"  # Unique prefix + safe name

    doc_type = instance.document_type  # 'timeline', 'budget', 'commitment'
    now = timezone.now()
    
    return f'proposal_documents/{doc_type}/{now.year}/{now.month}/{now.day}/{new_filename}'

class Proposal(Expression):
    """
    Propuesta formal: expresión aprobada con campos adicionales.
    Hereda todos los campos de Expression, más los nuevos.
    """
    # === NEW FIELDS SPECIFIC TO PROPOSAL ===

    project_title_override = models.TextField(
        blank=True,
        null=True,
        help_text="Si se especifica, sobrescribe el título de la expresión.",
        verbose_name="Título del Proyecto"
    )

    general_objective_override = models.TextField(
        blank=True,
        null = True,
        help_text="Si se especifica, sobrescribe el objetivo general de la expresión.",
    )

    thematic_axis_override = models.ForeignKey(
        'thematic_axes.ThematicAxis',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Si se especifica, sobrescribe el eje temático de la expresión.",
        verbose_name="Eje Temático",
        limit_choices_to={'is_active': True}
    )

    # Principal investigator role/title
    principal_investigator_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Título del Investigador Principal"
    )
    principal_investigator_position = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Cargo actual del Investigador Principal"
    )

    # Total_requested_budget (auto-calculated)
    total_requested_budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Presupuesto Total Solicitado"
    )

    # 1. Research Experience
    principal_research_experience = models.TextField(
        verbose_name="Experiencia en investigación del Investigador/a Principal",
        help_text="Máximo 250 palabras",
        max_length=1000,
        blank=True,
    )

    # 2. Partner Institutions (multiple) + Attachments
    partner_institutions = models.ManyToManyField(
        'institutions.Institution',
        verbose_name="Nombre y país de las instituciones aliadas",
        blank=True,
        related_name='proposals_as_partner',
    )
    partner_institution_commitments = models.ManyToManyField(
        'proposals.ProposalDocument',
        verbose_name="Cartas de compromiso institucional",
        blank=True,
        related_name='proposals_for_commitments',
    )

    # 3. Community and Country (text field + country dropdown)
    community_country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="País donde se desarrolla la comunidad",
        help_text="País de la comunidad involucrada",
        related_name='proposals_as_community_country', 
    )
    community_description = models.TextField(
        verbose_name="Comunidad y país",
        help_text="Descripción de la comunidad y su contexto",
        blank=True,
    )

    # 4. Project Location (country dropdown)
    project_location = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="País donde se desarrollará el proyecto",
        help_text="País principal de implementación",
        related_name='proposals_as_project_location',
    )

    # 5. Duration (months)
    duration_months = models.PositiveIntegerField(
        verbose_name="Duración del proyecto",
        help_text="Número de meses",
        validators=[MinValueValidator(1)],
        null=True,
        blank=True,
    )

    # 6. Summary (max 250 words)
    summary = models.TextField(
        verbose_name="Resumen",
        help_text="Síntesis descriptiva de la propuesta (máximo 250 palabras)",
        max_length=1000,
        blank=True,
    )

    # 7. Context, Problem & Justification (max 400 words)
    context_problem_justification = models.TextField(
        verbose_name="Contexto, problema y justificación",
        help_text="Máximo 400 palabras",
        max_length=1600,
        blank=True,
    )

    # # 8. Specific Objectives (max 200 words)
    # specific_objectives = models.TextField(
    #     verbose_name="Objetivos específicos",
    #     help_text="Máximo 200 palabras",
    #     max_length=800,
    #     blank=True,
    # )

    # 9. Methodology, Analytical Plan & Ethics (max 1500 words)
    methodology_analytical_plan_ethics = models.TextField(
        verbose_name="Metodología, planeamiento analítico y aspectos éticos",
        help_text="Máximo 1500 palabras",
        max_length=6000,
        blank=True,
    )

    # 10. Equity, Gender, Intersectionality, Inclusion (max 250 words)
    equity_inclusion = models.TextField(
        verbose_name="Equidad, género, interseccionalidad e inclusión",
        help_text="Máximo 250 palabras",
        max_length=1000,
        blank=True,
    )

    # 11. Timeline (file upload)
    timeline_document = models.ForeignKey(
        'proposals.ProposalDocument',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Cronograma",
        related_name='proposals_timeline',
        help_text="Archivo adjunto (PDF, DOCX)"
    )

    # 12. Communication Strategy (max 100 words)
    communication_strategy = models.TextField(
        verbose_name="Estrategia de comunicación",
        help_text="Máximo 100 palabras",
        max_length=400,
        blank=True,
    )

    # 13. Risk Analysis & Mitigation (max 200 words)
    risk_analysis_mitigation = models.TextField(
        verbose_name="Riesgos y plan de mitigación de riesgos",
        help_text="Máximo 200 palabras",
        max_length=800,
        blank=True,
    )

    # 14. Research Team (max 900 words)
    # research_team = models.TextField(
    #     verbose_name="Equipo de investigación",
    #     help_text="Máximo 900 palabras",
    #     max_length=3600,
    #     blank=True,
    # )

    # 15. Budget (file upload)
    budget_document = models.ForeignKey(
        'proposals.ProposalDocument',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Presupuesto",
        related_name='proposals_budget',
        help_text="Archivo adjunto (PDF, DOCX)"
    )

    # Generic relation for evaluations (keep from Expression)
    evaluations = GenericRelation(
        'evaluations.Evaluation',
        content_type_field='target_content_type',
        object_id_field='target_object_id',
        related_query_name='proposal'
    )

    proposal_status = models.ForeignKey(
        'common.Status',
        on_delete=models.PROTECT,
        verbose_name="Estado de la Propuesta",
        help_text="Estado del ciclo de vida de la propuesta (Borrador, Enviada, Aprobada, etc.)"
    )

    class Meta:
        verbose_name = "Propuesta"
        verbose_name_plural = "Propuestas"
        db_table = 'proposal'

    def __str__(self):
        return f"PROPUESTA: {self.project_title}"


class ProposalDocument(TimestampMixin, models.Model):
    """
    Document uploaded as part of the Proposal (e.g., timeline, budget, commitment letters).
    """
    proposal = models.ForeignKey(
        Proposal,
        on_delete=models.CASCADE,
        related_name='proposal_documents',
        verbose_name="Propuesta"
    )
    file = models.FileField(
        # upload_to='proposal_documents/%Y/%m/%d/',
        upload_to=proposal_file_upload_path,
        verbose_name="Archivo",
        help_text="Sube archivos como PDF, DOCX. Máximo 10MB.",
        max_length=500
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nombre del archivo"
    )
    uploaded_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Cargado por"
    )

    # Track which institution this document is for
    linked_institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Institución Asociada",
        help_text="Solo si el documento es específico para una institución (ej: carta de compromiso)"
    )


    document_type = models.CharField(
        max_length=50,
        choices=[
            ('timeline', 'Cronograma'),
            ('budget', 'Presupuesto'),
            ('commitment', 'Carta de Compromiso'),
        ],
        verbose_name="Tipo de Documento"
    )

    class Meta:
        db_table = 'proposal_document'
        verbose_name = "Documento de Propuesta"
        verbose_name_plural = "Documentos de Propuesta"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name or self.file.name} ({self.get_document_type_display()})"

    def save(self, *args, **kwargs):
        # Only set name if not already set and file exists
        if not self.name and self.file:
            self.name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

class ProposalSpecificObjective(TimestampMixin):
    """
    Objetivos específicos para la Propuesta.
    Pueden diferir de los de la Expresión.
    """
    proposal = models.ForeignKey(
        'proposals.Proposal',
        on_delete=models.CASCADE,
        related_name='specific_objectives'
    )
    title = models.CharField(max_length=200, verbose_name="Título")
    description = models.TextField(verbose_name="Descripción", blank=True)

    class Meta:
        db_table = 'proposal_specific_objective'
        verbose_name = "Objetivo Específico (Propuesta)"
        verbose_name_plural = "Objetivos Específicos (Propuesta)"

    def __str__(self):
        return f"{self.title} ({self.proposal})"