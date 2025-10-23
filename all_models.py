

# ===== From: experiences/models.py =====

from django.db import models
from core.models import TimestampMixin
from expressions.models import Expression
from accounts.models import User


class ExperienceType(TimestampMixin, models.Model):
    """
    Tipo de experiencia del líder del proyecto (ej: 'Investigación clínica', 'Gestión de proyectos').
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        db_table = 'experience_type'
        verbose_name = "Tipo de Experiencia"
        verbose_name_plural = "Tipos de Experiencia"
        ordering = ['name']

    def __str__(self):
        return self.name


class ProjectLeaderExperience(TimestampMixin, models.Model):
    """
    Experiencia del líder del proyecto en una categoría específica.
    """
    expression = models.ForeignKey( ## Esto es para la proposal no expresion
        'expressions.Expression', # PROPOSAL
        on_delete=models.CASCADE,
        verbose_name="Expresión de Interés"
    )
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        verbose_name="Usuario (Líder del Proyecto)"
    )
    experience_type = models.ForeignKey(
        ExperienceType,
        on_delete=models.PROTECT,
        verbose_name="Tipo de Experiencia"
    )
    description = models.TextField(verbose_name="Descripción de la Experiencia")
    academic_title = models.CharField(
        max_length=100,
        verbose_name="Título Académico"
    )
    current_position = models.CharField(
        max_length=100,
        verbose_name="Cargo Actual"
    )

    class Meta:
        db_table = 'project_leader_experience'
        verbose_name = "Experiencia del Líder del Proyecto"
        verbose_name_plural = "Experiencias del Líder del Proyecto"
        unique_together = ('expression', 'user', 'experience_type')
        ordering = ['expression__project_title', 'user__person__first_name', 'experience_type']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.experience_type.name}"

# ===== From: proposals/models.py =====

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

# ===== From: proponent_forms/models.py =====

from django.apps import apps
from django.db import models
from core.models import TimestampMixin
from core.choices import SOURCE_MODEL_CHOICES, FIELD_TYPE_CHOICES
from decimal import Decimal

class SharedQuestionCategory(TimestampMixin, models.Model):
    name = models.CharField(
        max_length=200, 
        verbose_name="Nombre", 
        unique=True
    )
    description = models.TextField(
        blank=True, 
        verbose_name="Descripción"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Activa"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        db_table = 'shared_question_category'
        verbose_name = "Categoría de Pregunta"
        verbose_name_plural = "Categorías de Pregunta"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
    

class SharedQuestion(TimestampMixin, models.Model):
    TARGET_CHOICES = [
        ('expression', 'Expresion de Interes'),
        ('proposal', 'Propuesta Completa')
    ]
    
    category = models.ForeignKey(
        'proponent_forms.SharedQuestionCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Categoría",
        related_name='questions'
    )

    question = models.TextField(verbose_name="Pregunta")

    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPE_CHOICES,
        default='text',
        verbose_name="Tipo de Campo"
    )

    options = models.JSONField(
        blank=True,
        null=True,
        verbose_name="Opciones Estaticas"
    )

    source_model = models.CharField(
        max_length=100,
        choices=SOURCE_MODEL_CHOICES,
        blank=True,
        null=True,
        verbose_name="Modelo de Origen"
    )

    target_category = models.CharField(
        max_length=20,
        choices=TARGET_CHOICES,
        verbose_name="Categoria Objetivo",
        help_text="Para que tipo de formulario se usa esta pregunta"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )

    is_required = models.BooleanField(
        default=True, 
        verbose_name="Requerida"
    )

    class Meta:
        db_table = 'shared_question'
        verbose_name = "Pregunta Compartida"
        verbose_name_plural = "Preguntas Compartidas"
        ordering = ['target_category', 'category__order', 'question']

    def __str__(self):
        cat = f" ({self.category})" if self.category else ""
        return f"{self.question}{cat} ({self.get_target_category_display()})"
    
    # def get_options(self):
    #     if self.field_type == 'dynamic_dropdown' and self.source_model:
    #         try:
    #             app_label, model_name = self.source_model.split('.')
    #             model = apps.get_model(app_label, model_name)
    #             return list(model.objects.values_list('name', flat=True))
    #         except (LookupError, AttributeError) as e:
    #             return [f"Error loading {self.source_model}: {e}"]
    #     elif self.options:
    #         return self.options
    #     return []

    def get_options(self):
        # Dynamic dropdown from source_model
        if self.field_type == 'dynamic_dropdown' and self.source_model:
            try:
                app_label, model_name = self.source_model.split('.')
                model = apps.get_model(app_label, model_name)
                for field in ['name', 'title', 'code', 'label', 'description']:
                    if hasattr(model, field):
                        return list(model.objects.values_list(field, flat=True))
                return [str(obj) for obj in model.objects.all()[:50]]
            except (LookupError, AttributeError) as e:
                return [f"Error loading {self.source_model}: {e}"]

        # Structured options (new system)
        if self.options_set.exists():
            return list(self.options_set.values_list('display_text', flat=True))

        # Legacy JSON options (simple list)
        if self.options:
            return self.options

        return []
    
    def get_scored_options(self):
        """Return list of (display_text, score) tuples."""
        if self.field_type == 'dynamic_dropdown':
            # Dynamic options don’t have scores (unless you extend them)
            return [(opt, Decimal('0.0')) for opt in self.get_options()]

        if self.options_set.exists():
            return list(self.options_set.values_list('display_text', 'score'))

        # Legacy options have no scores
        return [(opt, Decimal('0.0')) for opt in (self.options or [])]

class SharedQuestionOption(TimestampMixin, models.Model):
    shared_question = models.ForeignKey(
        'proponent_forms.SharedQuestion',
        on_delete=models.CASCADE,
        related_name='options_set',
        verbose_name='Pregunta Compartida'
    )

    display_text = models.CharField(
        max_length=200,
        verbose_name="Texto a mostrar"
    )
    
    score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal(0.0),
        verbose_name="Puntuación asociada (opcional)"
    )

    class Meta:
        verbose_name = "Opción de Pregunta Compartida"
        verbose_name_plural = "Opciones de Pregunta Compartida"
        ordering = ['shared_question', 'id']

    def __str__(self):
        return f"{self.display_text} ({self.score})"

class ProponentForm(TimestampMixin, models.Model):
    call = models.OneToOneField(
        'calls.Call',
        on_delete=models.CASCADE,
        verbose_name="Convocatoria"
    )

    title = models.CharField(
        max_length=200, 
        verbose_name="Título"
    )

    is_active = models.BooleanField(
        default=True, 
        verbose_name="Activo"
    )

    class Meta:
        db_table = 'proponent_form'
        verbose_name = "Formulario del Proponente"
        verbose_name_plural = "Formularios del Proponente"

    def __str__(self):
        return f"Form: {self.call.title}"

class ProponentFormQuestion(TimestampMixin, models.Model):
    """
    relacion entre un formulario y una pregunta compartida.
    Permite orden y posibles overrides en el futuro.
    """
    form = models.ForeignKey(
        'proponent_forms.ProponentForm',
        on_delete=models.CASCADE,
        related_name="form_questions",
        verbose_name="Formulario"
    )

    shared_question = models.ForeignKey(
        'proponent_forms.SharedQuestion',
        on_delete=models.CASCADE,
        verbose_name="Pregunta Compartida"
    )

    order = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Orden"
    )

    class Meta:
        db_table = 'proponent_form_question'
        ordering = ['order']
        unique_together = ('form', 'shared_question')
        verbose_name = "Pregunta del Formulario"
        verbose_name_plural = "Preguntas del Formulario"

    def __str__(self):
        return f"{self.form} - {self.shared_question}"
        
class ProponentResponse(TimestampMixin, models.Model):
    expression = models.ForeignKey(
        'expressions.Expression',
        on_delete=models.CASCADE,
        verbose_name="Expresión de Interés",
        related_name='form_responses'
    )

    shared_question = models.ForeignKey(
        'proponent_forms.SharedQuestion',
        on_delete=models.CASCADE,
        verbose_name="Pregunta Compartida"
    )

    value = models.JSONField(
        null=True, 
        blank=True,
        verbose_name="Valor"
    )

    score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name="Puntuación derivada"
    )

    comment = models.TextField(
        blank=True,
        verbose_name="Comentario"
    )

    class Meta:
        unique_together = ('expression', 'shared_question')
        db_table = 'proponent_response'
        verbose_name = "Respuesta del Proponente"
        verbose_name_plural = "Respuestas del Proponente"

    def __str__(self):
        return f"Respuesta: {self.expression.project_title}"


# ===== From: people/models.py =====

from django.db import models
from django.contrib.auth import get_user_model
from core.models import TimestampMixin, CreatedByMixin, AddressMixin
from geo.models import DocumentType

User = get_user_model()



class Person(TimestampMixin, CreatedByMixin, models.Model):
    
    id = models.AutoField(
        primary_key=True,
        verbose_name="ID Persona"
    )

    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        verbose_name="Tipo de documento",
        db_index=True
    )

    document_number = models.CharField(
        max_length=50, 
        unique=True, 
        verbose_name="Numero de documento", 
        db_index=True
    )

    first_name = models.CharField(
        max_length=32, 
        verbose_name="Primer nombre"
    )

    second_name = models.CharField(
        max_length=32, 
        verbose_name="Segundo nombre", 
        blank=True, 
        null=True
    )

    first_last_name = models.CharField(
        max_length=32, 
        verbose_name="Primer apellido"
    )

    second_last_name = models.CharField(
        max_length=32, 
        verbose_name="Segundo apellido", 
        blank=True, 
        null=True
    )

    
    GENDER_CHOICES = [
        ('F', 'Femenino'),
        ('M', 'Masculino'),
        ('O', 'Otro'),
        ('N', 'Prefiero no decir'),
    ]

    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        verbose_name='Genero'
    )

    class Meta:
        db_table = 'person'
        verbose_name = 'Persona'
        verbose_name_plural = 'Personas'

    def __str__(self):
        return f"{self.first_name} {self.first_last_name}"
    
    def get_full_name(self):
        """Return full name (first + second name + both last names)."""
        parts = [
            self.first_name,
            getattr(self, "second_name", None),  # in case it's optional
            self.first_last_name,
            getattr(self, "second_last_name", None),
        ]
        # filter out None or empty strings
        return " ".join(filter(None, parts)).strip()

    def get_short_name(self):
        """Return first name only"""
        return self.first_name


# ===== From: thematic_axes/models.py =====

from django.db import models
from core.models import TimestampMixin, CreatedByMixin

class ThematicAxis(TimestampMixin, CreatedByMixin, models.Model):
    name = models.CharField(
        max_length=250, 
        unique=True,
        verbose_name="Nombre Eje Tematico"
    )

    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Descripcion"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )


    class Meta:
        db_table = 'thematic_axis'
        verbose_name = 'Eje Temático'
        verbose_name_plural = 'Ejes Temáticos'
        ordering = ['name']

    def __str__(self):
        return self.name

# ===== From: core/models.py =====

from django.db import models
from django.contrib.auth.models import User

class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha Creacion', db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha Actualizacion')

    class Meta:
        abstract = True

class AddressMixin(models.Model):
    address_line1 = models.CharField(max_length=255, blank=True, verbose_name="Address Line 1")
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name="Address Line 2")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ciudad")
    state = models.CharField(max_length=100, blank=True, verbose_name="Departamento/Provincia")
    # country = models.CharField(max_length=100, blank=True, verbose_name="Pais")

    class Meta:
        abstract=True

class CreatedByMixin(models.Model):
    created_by = models.ForeignKey(
        # 'accounts.CustomUser',
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name="%(app_label)s_%(class)s_created"
    )
    
    class Meta:
        abstract=True




# ===== From: expressions/models.py =====

from django.db import models

#from django.contrib.auth.models import AbstractUser

from django.db import models
from core.models import TimestampMixin, CreatedByMixin
from django.core.validators import RegexValidator
from django.core.files.storage import default_storage
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation

class Expression(TimestampMixin, CreatedByMixin, models.Model):
    id = models.AutoField(
        primary_key=True,
        verbose_name="ID Rol"
    )
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        verbose_name="Usuario"
    )

    call = models.ForeignKey(
        'calls.Call',
        on_delete=models.CASCADE,
        verbose_name="Convocatoria"
    )

    thematic_axis = models.ForeignKey(
        'thematic_axes.ThematicAxis',
        on_delete=models.PROTECT,
        verbose_name="Eje Temático"
    )
    status = models.ForeignKey(
        'common.Status',
        on_delete=models.PROTECT,
        verbose_name="Estado"
    )
    project_title = models.TextField(
        verbose_name="Título del Proyecto"
    )
    implementation_country = models.ForeignKey(
        'geo.Country',
        on_delete=models.PROTECT,
        verbose_name="País de Implementación"
    )

    primary_institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.PROTECT,
        related_name='expressions_as_primary',
        blank=True,
        null=True
    )

    problem = models.TextField(
        verbose_name="Descripción del Problema"
    )

    general_objective = models.TextField(
        verbose_name="Objetivo General"
    )

    methodology = models.TextField(
        verbose_name="Metodología"
    )

    funding_eligibility_acceptance = models.BooleanField(
        default=False,
        verbose_name="Aceptación de Elegibilidad para Financiamiento"
    )

    submission_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Envío"
    )

    scale = models.ForeignKey(
        'common.Scale',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Escala del Presupuesto"
    )

    intersectionality_scopes = models.ManyToManyField(
        'intersectionality.IntersectionalityScope',
        blank=True,
        related_name='expressions',
        verbose_name="Ámbitos de Interseccionalidad"
    )

    community_organization = models.ForeignKey(
        'cbo.CBO',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Organización Comunitaria (CBO)",
        related_name='proposals'  # now each CBO can be linked to many proposals
    )
    
    evaluations = GenericRelation(
        'evaluations.Evaluation',
        content_type_field='target_content_type',
        object_id_field='target_object_id',
        related_query_name='expression'
    )


    # evaluations = models.ManyToManyField(
    #     'accounts.CustomUser',
    #     through='evaluations.Evaluation',
    #     through_fields=('expression', 'evaluator')
    #     related_name='evaluated_expressions'
    # )

    # expression.evaluation_set.all()  # All evaluations for this expression
    # user.evaluated_expressions.all()  # All expressions this user evaluated

    class Meta:
        db_table = 'expression'
        verbose_name = 'Expresión de Interés'
        verbose_name_plural = 'Expresiones de Interés'
        ordering = ['-submission_datetime', '-created_at']

    def __str__(self):
        return self.project_title

    def save(self, *args, **kwargs):
        # Auto-set submission_datetime on first save (when status changes to submitted)
        # Only apply logic if status is set
        if self.pk:  # Updating existing Expression/Proposal
            try:
                # Always look in Expression table
                old = Expression.objects.get(pk=self.pk)
                # print("Old is:",old)
                # print("Old.created_at is:", old.created_at)
                # print("Old.user_id is:", old.user_id)
                if old.created_at:
                    self.created_at = old.created_at
            except Expression.DoesNotExist:
                pass

        if self.status_id and not self.submission_datetime:
            if self.status.name.lower() == 'submitted':
                self.submission_datetime = self.updated_at

        super().save(*args, **kwargs)
    
    @property
    def evaluations(self):
        """Get all evaluations for this expression via GenericForeignKey."""
        from evaluations.models import Evaluation
        content_type = ContentType.objects.get_for_model(self)
        return Evaluation.objects.filter(
            target_content_type=content_type,
            target_object_id=self.id
        )

    # Get first evaluation
    @property
    def first_evaluation(self):
        return self.evaluations.first()

class ExpressionDocument(TimestampMixin, models.Model):
    """
    Document uploaded by the researcher as part of their Expression.
    Stored temporarily until submission. Deleted on submission or timeout.
    """
    expression = models.ForeignKey(
        'Expression',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Expresión de Interés"
    )
    file = models.FileField(
        upload_to='expression_documents/%Y/%m/%d/',
        verbose_name="Archivo",
        help_text="Sube archivos como CV, cartas de apoyo, certificados. Máximo 10MB."
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

    class Meta:
        db_table = 'expression_document'
        verbose_name = "Documento de Expresión"
        verbose_name_plural = "Documentos de Expresión"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name or self.file.name} ({self.expression.project_title})"
    
    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.file.name
        super().save(*args, **kwargs)

# ===== From: intersectionality/models.py =====

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

# ===== From: institutions/models.py =====

from django.db import models
from core.models import TimestampMixin, AddressMixin, CreatedByMixin
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

class InstitutionType(TimestampMixin, CreatedByMixin):
    """
    Representa las categorias de una institucion.
    """
    id = models.AutoField(primary_key=True)

    name = models.CharField(
        max_length=100,
        verbose_name=("Nombre Institucion")
    )

    # order = models.PositiveBigIntegerField(
    #     ("Order"),
    #     default=0,
    #     db_index=True
    # )

    is_active = models.BooleanField(
        ("Activa"),
        default=True,
        help_text=("Al deshabilitarse, no aparecera en las listas de seleccion.")
    )

    class Meta:
        verbose_name = "Tipo de Institucion"
        verbose_name_plural = "Tipos de institucion"
        ordering = ['id', 'name']

    def __str__(self):
        return self.name

class Institution(TimestampMixin, AddressMixin, CreatedByMixin):
    """
    Representa una organizacion.
    """
    id = models.AutoField(primary_key=True)

    institution_type = models.ForeignKey(
        'InstitutionType',
        on_delete=models.PROTECT,
        verbose_name=("Tipo")
    )

    legal_representative = models.ForeignKey(
        'people.Person',
        on_delete=models.SET_NULL,
        verbose_name="Representante Legal",
        blank=True,
        null=True,
        related_name='legal_represented_institutions'
    )

    administrative_representative = models.ForeignKey(
        'people.Person',
        on_delete=models.SET_NULL,
        verbose_name="Representante Administrativo",
        blank=True,
        null=True,
        related_name='administrative_represented_institutions'
    )

    country = models.ForeignKey(
        'geo.Country',
        on_delete=models.SET_NULL,
        related_name='institutions',
        blank=True,
        null=True
    )

    name = models.CharField(
        "Nombre de institucion",
        max_length=200
    )

    acronym = models.CharField("Acronym", max_length=50, blank=True)
    website = models.URLField("Website", blank=True)

    tax_register_number = models.CharField(
        "Numero de Registro Tributario",
        max_length=50,
        help_text="NUmero de registro tributario."
    )

    phone_number = models.CharField(
        "Teléfono",
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{7,15}$',
                message="Ingrese un número de teléfono válido (7 a 15 dígitos, puede incluir + al inicio)."
            )
        ],
        help_text="Ejemplo: +573001234567"
    )

    is_active = models.BooleanField(
        ("Activa"),
        default=True,
        db_index=True,
        help_text=_("Marque como inactivo en lugar de eliminar")
    )



    class Meta:
        verbose_name = _("Institución")
        verbose_name_plural = _("Instituciones")
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'country'],
                name='unique_institution_per_country'
            )
        ]

    def __str__(self):
        return self.name
    
    # For detail views
    # Defining the URL pattern is needed
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('institutions:detail', kwargs={'pk': self.pk})

# ===== From: antecedents/models.py =====

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

# ===== From: strategic_effects/models.py =====

from django.db import models
from core.models import TimestampMixin, CreatedByMixin
from thematic_axes.models import ThematicAxis

class StrategicEffect(TimestampMixin, CreatedByMixin, models.Model):
    """
    Efecto estrategico predefinido en la documentacion.
    """
    name = models.CharField(
        max_length=500,
        unique=True,
        verbose_name="Nombre"
    )

    description = models.TextField(
        blank=True, 
        verbose_name="Descripcion"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    thematic_axis = models.ForeignKey(
        'thematic_axes.ThematicAxis',
        on_delete=models.PROTECT,
        verbose_name="Eje Temático",
        help_text="Eje temático al que pertenece este efecto estratégico"
    )

    class Meta:
        db_table = 'strategic_effect'
        verbose_name="Efecto Estrategico"
        verbose_name_plural="Efectos Estrategicos"
        ordering = ['thematic_axis__name', 'name']

    def __str__(self):
        return self.name
    

# LOAD VIA FIXTURES (TEMPLATE)

# [
#   {
#     "model": "common.strategiceffect",
#     "fields": {
#       "name": "Desarrollo Económico Local",
#       "description": "Impulso a la economía en comunidades vulnerables."
#     }
#   },
#   {
#     "model": "common.strategiceffect",
#     "fields": {
#       "name": "Innovación Tecnológica",
#       "description": "Generación de nuevas tecnologías o procesos."
#     }
#   }
# ]

# ===== From: products/models.py =====

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

# ===== From: calls/models.py =====

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

# ===== From: project_team/models.py =====

from django.db import models
from core.models import TimestampMixin
# from expressions.models import Expression
# from people.models import Person
# from common.models import Status
# from thematic_axes.models import ThematicAxis


class BaseProjectTeamMember(TimestampMixin, models.Model):
    """
    Miembro del equipo de proyecto asignado a una Expresión de Interés.
    Define su rol, fechas y estado.
    """
    person = models.ForeignKey(
        'people.Person',
        on_delete=models.PROTECT,
        verbose_name="Persona"
    )
    role = models.CharField(
        max_length=100,
        verbose_name="Rol en el Proyecto"
    )
    status = models.ForeignKey(
        'common.Status',
        on_delete=models.PROTECT,
        verbose_name="Estado de Participación",
        null=True,  # Allow null until selected/created
        blank=True,
    )
    institution = models.ForeignKey(
        'institutions.Institution',
        on_delete=models.PROTECT,
        verbose_name="Institución",
        null=True,  # Allow null until selected/created
        blank=True,
    )
    start_date = models.DateField(verbose_name="Fecha de Inicio", blank=True, null=True)
    end_date = models.DateField(verbose_name="Fecha de Finalización", blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.person} - {self.role} ({self.institution.name if self.institution else 'Sin Institución'})"
    
class ExpressionTeamMember(BaseProjectTeamMember, models.Model):
    expression = models.ForeignKey(
        'expressions.Expression',
        on_delete=models.PROTECT,
        related_name='expression_team_members',
        verbose_name="Expresión"
    )

    class Meta:
        db_table = 'expression_teammember'
        verbose_name = "Miembro del Equipo (Expresión)"
        verbose_name_plural = "Miembros del Equipo (Expresión)"
        unique_together = ('expression', 'person')
        ordering = ['expression', 'role']

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

class ProposalTeamMember(BaseProjectTeamMember):
    """
    Team member linked to a Formal Proposal.
    Can be modified independently from Expression version.
    """
    proposal = models.ForeignKey(
        'proposals.Proposal',
        on_delete=models.PROTECT,
        related_name='proposal_team_members',
        verbose_name="Propuesta"
    )

    # Upload CV for this member
    cv_file = models.FileField(
        upload_to='proposal_team_cv/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name="C.V. Adjunto"
    )

    class Meta:
        db_table = 'proposal_teammember'
        verbose_name = "Miembro del Equipo (Propuesta)"
        verbose_name_plural = "Miembros del Equipo (Propuesta)"
        unique_together = ('proposal', 'person')
        ordering = ['proposal', 'role']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def has_cv(self):
        return bool(self.cv_file)


class BaseInvestigatorThematicAntecedent(TimestampMixin, models.Model):
    description = models.TextField(verbose_name="Descripción del Antecedente")
    evidence_url = models.URLField(
        blank=True,
        verbose_name="URL de Evidencia"
    )

    class Meta:
        abstract=True

class ExpressionInvestigatorThematicAntecedent(BaseInvestigatorThematicAntecedent):
    """
    Antecedente del investigador en un eje temático específico.
    Asociado con un miembro de la Expresión.
    """
    team_member = models.ForeignKey(
        'project_team.ExpressionTeamMember',
        on_delete=models.CASCADE,
        related_name='expression_thematic_antecedents',
        verbose_name="Miembro del Equipo (Expresión)"
    )
    thematic_axis = models.ForeignKey(
        'thematic_axes.ThematicAxis',
        on_delete=models.PROTECT,
        verbose_name="Eje Temático",
        blank=True,
        null=True
    )    

    class Meta:
        db_table = 'investigator_thematic_antecedent'
        verbose_name = "Antecedente en Eje Temático (Expresión)"
        verbose_name_plural = "Antecedentes en Ejes Temáticos (Expresión)"

    def __str__(self):
        return f"{self.team_member.person} - {self.thematic_axis}"

class ProposalInvestigatorThematicAntecedent(BaseInvestigatorThematicAntecedent):
    """
    Antecedente temático para un miembro de la Propuesta.
    Permite diferencias respecto a la Expresión.
    """
    team_member = models.ForeignKey(
        'project_team.ProposalTeamMember',
        on_delete=models.CASCADE,
        related_name='proposal_thematic_antecedents',
        verbose_name="Miembro del Equipo (Propuesta)"
    )
    thematic_axis = models.ForeignKey(
        'thematic_axes.ThematicAxis',
        on_delete=models.PROTECT,
        verbose_name="Eje Temático",
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'proposal_investigator_antecedent'
        verbose_name = "Antecedente en Eje Temático (Propuesta)"
        verbose_name_plural = "Antecedentes en Ejes Temáticos (Propuesta)"

    def __str__(self):
        return f"{self.team_member.person} - {self.thematic_axis}"


class InvestigatorCondition(TimestampMixin, models.Model):
    """
    Condición específica de participación del investigador.
    """
    team_member = models.ForeignKey(
        'project_team.ExpressionTeamMember',
        on_delete=models.CASCADE,
        related_name='conditions',
        verbose_name="Miembro del Equipo"
    )
    condition_text = models.TextField(verbose_name="Condición")
    is_fulfilled = models.BooleanField(
        default=False,
        verbose_name="Cumplida"
    )
    fulfillment_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Cumplimiento"
    )

    class Meta:
        db_table = 'investigator_condition'
        verbose_name = "Condición del Investigador"
        verbose_name_plural = "Condiciones de los Investigadores"

    def __str__(self):
        return f"Condición: {self.condition_text[:50]}... ({'Sí' if self.is_fulfilled else 'No'})"

# ===== From: geo/models.py =====

from django.db import models

class Country(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name="Nombre Pais", max_length=100, unique=True)
    phone_number_indicative = models.CharField(verbose_name="Indicativo", max_length=6)


    class Meta:
        db_table = 'country'
        verbose_name = "Pais"
        verbose_name_plural = "Paises"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.phone_number_indicative})"
    
class DocumentType(models.Model):
    id = models.AutoField(primary_key=True)
    country = models.ForeignKey(
        'geo.Country',
        on_delete=models.CASCADE,
        db_column='country_id',
        related_name='document_types',
        verbose_name='Paises'
    )
    
    name = models.CharField("Nombre de Tipo de Documento", max_length=100)

    class Meta:
        db_table = 'document_type'
        verbose_name = "Tipo Documento"
        verbose_name_plural = "Tipos Documento"
        unique_together = ('country', 'name')
        ordering = ['country', 'name']

def __str__(self):
    return f"{self.name} ({self.country.name})"

# ===== From: cbo/models.py =====

from django.db import models
from core.models import TimestampMixin

from django.core.validators import RegexValidator

phone_regex = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="El número debe estar en formato internacional."
)


class CBO(TimestampMixin, models.Model):
    """
    Organización Comunitaria (CBO) vinculada a una Expresión de Interés.
    """
    name = models.CharField(max_length=150, verbose_name="Nombre")
    description = models.TextField(verbose_name="Descripción")
    number_of_members = models.PositiveIntegerField(verbose_name="Número de Miembros")
    contact_person_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Nombre de Persona de Contacto"
    )
    contact_phone = models.CharField(
        max_length=17,
        blank=True,
        verbose_name="Teléfono de Contacto"
    )
    contact_email = models.EmailField(
        blank=True,
        verbose_name="Correo de Contacto"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )

    class Meta:
        db_table = 'cbo'
        verbose_name = "Organización Comunitaria (CBO)"
        verbose_name_plural = "Organizaciones Comunitarias (CBOs)"
        ordering = ['name']

    def __str__(self):
        return self.name


class CBOAntecedent(TimestampMixin, models.Model):
    """
    Proyecto anterior en el que participó la CBO.
    """
    cbo = models.ForeignKey(
        'cbo.CBO',
        on_delete=models.CASCADE,
        related_name='antecedents',
        verbose_name="CBO"
    )
    project_name = models.CharField(max_length=200, verbose_name="Nombre del Proyecto")
    description = models.TextField(verbose_name="Descripción")
    year = models.PositiveIntegerField(verbose_name="Año")
    funding_source = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Fuente de Financiamiento"
    )
    outcomes = models.TextField(verbose_name="Resultados")

    class Meta:
        db_table = 'cbo_antecedent'
        verbose_name = "Antecedente de CBO"
        verbose_name_plural = "Antecedentes de CBO"
        ordering = ['-year', 'project_name']

    def __str__(self):
        return f"{self.project_name} ({self.year})"


class CBORelevantRole(TimestampMixin, models.Model):
    """
    Rol relevante dentro de la CBO (ej: Presidente, Coordinador).
    Permite roles predefinidos o personalizados.
    """
    PREDEFINED_ROLE_CHOICES = [
        ('president', 'Presidente'),
        ('vice_president', 'Vicepresidente'),
        ('coordinator', 'Coordinador'),
        ('treasurer', 'Tesorero'),
        ('secretary', 'Secretario'),
        ('member', 'Miembro'),
    ]

    cbo = models.ForeignKey(
        'cbo.CBO',
        on_delete=models.CASCADE,
        related_name='roles',
        verbose_name="CBO"
    )
    predefined_role = models.CharField(
        max_length=20,
        choices=PREDEFINED_ROLE_CHOICES,
        blank=True,
        null=True,
        verbose_name="Rol Predefinido"
    )
    custom_role = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Rol Personalizado"
    )
    person_name = models.CharField(max_length=100, verbose_name="Nombre de la Persona")
    contact_phone = models.CharField(
        max_length=17,
        blank=True,
        verbose_name="Teléfono"
    )
    contact_email = models.EmailField(
        blank=True,
        verbose_name="Correo Electrónico"
    )

    class Meta:
        db_table = 'cbo_relevant_role'
        verbose_name = "Rol Relevante de CBO"
        verbose_name_plural = "Roles Relevantes de CBO"
        ordering = ['predefined_role', 'custom_role']

    def __str__(self):
        return f"{self.get_role_display()} - {self.person_name}"

    def get_role_display(self):
        if self.predefined_role:
            return self.get_predefined_role_display()
        return self.custom_role or "Sin rol"

    def clean(self):
        from django.core.exceptions import ValidationError
        super().clean()
        if not self.predefined_role and not self.custom_role:
            raise ValidationError("Debe seleccionar un rol predefinido o ingresar uno personalizado.")
        if self.predefined_role and self.custom_role:
            raise ValidationError("No puede seleccionar un rol predefinido y uno personalizado al mismo tiempo.")

# ===== From: budgets/models.py =====

from django.db import models
from core.models import TimestampMixin, CreatedByMixin
from expressions.models import Expression
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

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

class BaseBudgetItem(models.Model):
    """
    Ítem de presupuesto para una expresión.
    Relaciona categoría, período y monto.
    Base abstracta para cualquier Ítem de presupuesto.
    Permite compartir la estructura entre la expresión y la propuesta.
    """
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
        abstract = True  # This prevents DB table creation

    def clean(self):
        if self.amount < 0:
            raise ValidationError("El monto no puede ser negativo.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class BudgetItem(TimestampMixin, BaseBudgetItem):
    expression = models.ForeignKey(
        'expressions.Expression',
        on_delete=models.CASCADE,
        verbose_name="Expresión de Interés"
    )

    class Meta:
        db_table = 'budget_item'
        verbose_name = "Ítem de Presupuesto (Expresión)"
        verbose_name_plural = "Ítems de Presupuesto (Expresión)"
        unique_together = ('expression', 'category', 'period')
        ordering = ['category__name', 'period__order']

    def __str__(self):
        return f"{self.expression.project_title} - {self.category.name} ({self.period.name}): {self.amount}"

class ProposalBudgetItem(TimestampMixin, BaseBudgetItem):
    proposal = models.ForeignKey(
        'proposals.Proposal',
        on_delete=models.CASCADE,
        related_name='budget_items'
    )

    class Meta(BaseBudgetItem.Meta):
        db_table = 'proposal_budget_item'
        verbose_name = "Ítem de Presupuesto (Propuesta)"
        verbose_name_plural = "Ítems de Presupuesto (Propuesta)"
        unique_together = ('proposal', 'category', 'period')
        ordering = ['category__name', 'period__order']

    def __str__(self):
        return f"{self.proposal.project_title} - {self.category.name} ({self.period.name}): {self.amount}"
    


# ===== From: evaluations/models.py =====

from django.db import models
from django.apps import apps
from core.models import TimestampMixin, CreatedByMixin
from core.choices import FIELD_TYPE_CHOICES, SOURCE_MODEL_CHOICES
from expressions.models import Expression
from accounts.models import CustomUser
from common.models import Status
from calls.models import Call
from django.contrib.contenttypes.fields import GenericForeignKey
from decimal import Decimal

class EvaluationTemplate(TimestampMixin, CreatedByMixin, models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Descripcion"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )

    # Template can be used for Expression, Proposal, or both
    applies_to_expression = models.BooleanField(
        default=True,
        verbose_name="Aplica a Expresiones"
    )
    applies_to_proposal = models.BooleanField(
        default=True,
        verbose_name="Aplica a Propuestas"
    )

    # Template is tied to one or more calls
    calls = models.ManyToManyField(
        'calls.Call',
        blank=True,
        related_name='evaluation_templates',
        verbose_name="Convocatorias Aplicables"
    )

    class Meta:
        db_table = 'evaluation_template'
        verbose_name = "Plantilla de Evaluacion"
        verbose_name_plural = "Plantillas de Evaluacion"
        ordering = ['name']

    def __str__(self):
        return self.name
    
    def get_total_max_score(self):
        """Calculate the sum of max_score from all items."""
        return self.categories.aggregate(
            total=models.Sum('subcategories__items__max_score')
        )['total'] or 0

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalculate max_possible_score for all evaluations using this template
        self.update_evaluations()

    def update_evaluations(self):
        """Recalculate max_possible_score and re-evaluate is_positive for all related evaluations."""
        new_total = self.get_total_max_score()

        # If there are no items, set to 0
        if new_total is None:
            new_total = 0

        # Grab all evaluations tied to this template
        evaluations = Evaluation.objects.filter(template=self).select_related("status")

        for evaluation in evaluations:
            evaluation.max_possible_score = new_total

            # Only recalc is_positive if evaluation is completed and has a score
            if evaluation.status.name == "Completada" and evaluation.total_score is not None:
                ratio = Decimal(str(evaluation.total_score)) / Decimal(str(new_total)) if new_total > 0 else Decimal("0")
                evaluation.is_positive = ratio >= Decimal("0.7")

            evaluation.save(update_fields=["max_possible_score", "is_positive"])
            
    # def update_evaluations(self):
    #     """Update all Evaluation objects using this template with new max_possible_score."""
    #     total = self.get_total_max_score()
    #     if total > 0:
    #         Evaluation.objects.filter(template=self).update(max_possible_score=total)

    # def update_evaluations(self):
    #     """Recalculate max_possible_score and re-evaluate is_positive for all related evaluations."""
    #     new_total = self.get_total_max_score()
    #     if new_total == 0:
    #         return

    #     # Get all evaluations using this template
    #     evaluations = Evaluation.objects.filter(template=self).select_related('target', 'status')

    #     for eval in evaluations:
    #         # Update max possible score
    #         eval.max_possible_score = new_total

    #         # Recalculate is_positive only if it was Completada
    #         if eval.status.name == 'Completada' and eval.total_score is not None:
    #             ratio = Decimal(str(eval.total_score)) / Decimal(str(new_total))
    #             eval.is_positive = ratio >= Decimal('0.7')  # 70%

    #         eval.save(update_fields=['max_possible_score', 'is_positive'])

class TemplateCategory(TimestampMixin, models.Model):
    template = models.ForeignKey(
        EvaluationTemplate,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name="Plantilla"
    )

    name = models.CharField(
        max_length=400, 
        verbose_name="Nombre"
    )

    # weight = models.DecimalField(
    #     max_digits=3,
    #     decimal_places=1,
    #     default=1.0,
    #     help_text="Peso relativo de esta categoría en la evaluación (ej: 30.0 = 30%)",
    #     verbose_name="Peso (%)"
    # )

    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    is_active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )

    class Meta:
        ordering = ['order']
        verbose_name = "Categoría de Plantilla"
        verbose_name_plural = "Categorías de Plantilla"

    def __str__(self):
        return self.name

class TemplateSubcategory(TimestampMixin, models.Model):
    category = models.ForeignKey(
        TemplateCategory, 
        on_delete=models.CASCADE, 
        related_name='subcategories', 
        verbose_name="Categoría"
    )
    name = models.CharField(max_length=400, verbose_name="Nombre")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    is_active = models.BooleanField(default=True, verbose_name='Activa')

    class Meta:
        ordering = ['order']
        verbose_name = "Subcategoría de Plantilla"
        verbose_name_plural = "Subcategorías de Plantilla"

    def __str__(self):
        return f"{self.category.name}: {self.name}"
    
class TemplateItem(TimestampMixin, models.Model):
    """
    Ítem de evaluación (pregunta) dentro de una categoría.
    Define el tipo de entrada esperado.
    """

    subcategory = models.ForeignKey(
        TemplateSubcategory, 
        on_delete=models.CASCADE, 
        related_name='items', 
        verbose_name="Subcategoría"
    )
    question = models.TextField(verbose_name="Pregunta")
    field_type = models.CharField(
        max_length=20, 
        choices=FIELD_TYPE_CHOICES, 
        default='text', 
        verbose_name="Tipo de Campo"
    )
    source_model = models.CharField(
        max_length=100, 
        choices=SOURCE_MODEL_CHOICES, 
        blank=True, 
        null=True, 
        verbose_name="Modelo de Origen"
    )
    max_score = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        default=5.0, 
        verbose_name="Puntuación Máxima"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering = ['order']
        verbose_name = "Ítem de Plantilla"
        verbose_name_plural = "Ítems de Plantilla"

    def __str__(self):
        return f"{self.subcategory}: {self.question}"
    
    def calculate_max_score_from_options(self):
        """Return the highest score among this item's options, or None if no options."""
        if self.options.exists():
            result = self.options.aggregate(max_score=models.Max('score'))['max_score']
            return result
        return None
    
    def sync_max_score(self):
        """Update max_score from options and save if changed."""
        new_max = self.calculate_max_score_from_options()
        if new_max is not None and self.max_score != new_max:
            self.max_score = new_max
            self.save(update_fields=['max_score'])

    def get_dynamic_options(self):
        """Fetch display values from source_model (for UI prefill)."""
        if self.field_type == 'dynamic_dropdown' and self.source_model:
            try:
                app_label, model_name = self.source_model.split('.')
                model = apps.get_model(app_label, model_name)
                for field in ['name', 'title', 'code', 'label', 'description']:
                    if hasattr(model, field):
                        return list(model.objects.values_list('id', field))
                return [(obj.pk, str(obj)) for obj in model.objects.all()[:50]]
            except Exception:
                return []
        return []

    def get_options(self):
        if self.field_type == 'dynamic_dropdown' and self.source_model:
            try:
                app_label, model_name = self.source_model.split('.')
                model = apps.get_model(app_label, model_name)
                
                # Try common field names
                for field in ['name', 'title', 'code', 'label', 'description']:
                    if hasattr(model, field):
                        return list(model.objects.values_list(field, flat=True))
                
                # Fallback to str representation
                return [str(obj) for obj in model.objects.all()[:50]]
                
            except (LookupError, AttributeError) as e:
                return [f"Error loading {self.source_model}: {e}"]
        elif self.options:
            return self.options
        return []

class TemplateItemOption(TimestampMixin, models.Model):
    item = models.ForeignKey(
        TemplateItem, 
        on_delete=models.CASCADE, 
        related_name='options', 
        verbose_name="Ítem"
    )
    display_text = models.CharField(
        max_length=200, 
        verbose_name="Texto a mostrar"
    )
    score = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        default=0.0, 
        verbose_name="Puntuación asociada"
    )
    source_object_id = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="ID del objeto si proviene de source_model"
    )

    class Meta:
        verbose_name = "Opción de Ítem"
        verbose_name_plural = "Opciones de Ítem"
        ordering = ['item', 'id']

    def __str__(self):
        return f"{self.display_text}: {self.score}"

class Evaluation(TimestampMixin, CreatedByMixin, models.Model):
    """
    Evaluación realizada por un evaluador.
    Puede ser sobre una Expresión o una Propuesta.
    """
    # Generic foreign key to either Expression or Proposal
    target_content_type = models.ForeignKey(
        'contenttypes.ContentType',
        on_delete=models.CASCADE,
        limit_choices_to={
            'model__in': ['expression', 'proposal']
        },
        verbose_name="Objetivo"
    )
    target_object_id = models.PositiveIntegerField(verbose_name="ID del Objetivo")
    target = GenericForeignKey('target_content_type', 'target_object_id')

    evaluator = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.PROTECT,
        verbose_name="Evaluador"
    )
    status = models.ForeignKey(
        'common.Status',
        on_delete=models.PROTECT,
        verbose_name="Estado"
    )
    template = models.ForeignKey(
        'evaluations.EvaluationTemplate',
        on_delete=models.PROTECT,
        verbose_name="Plantilla de Evaluación"
    )
    total_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Puntuación Total"
    )
    max_possible_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        verbose_name="Puntuación Máxima Posible"
    )
    submission_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Envío"
    )

    # Track if this evaluation is considered "positive"
    is_positive = models.BooleanField(
        default=False,
        verbose_name="Evaluación positiva"
    )

    # Coordinator can mark evaluation as "validated" after review
    is_validated = models.BooleanField(
        default=False,
        verbose_name="Validada por coordinador"
    )

    # Optional: Coordinator notes
    coordinator_notes = models.TextField(
        blank=True,
        verbose_name="Notas del coordinador"
    )

    class Meta:
        unique_together = ('target_content_type', 'target_object_id', 'evaluator')
        db_table = 'evaluation'
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        ordering = ['-submission_datetime']

    def __str__(self):
        if self.target_content_type.model == "expression":
            return f"Evaluación de la expresión '{self.target.project_title}' por {self.evaluator}"
        elif self.target_content_type.model == "proposal":
            return f"Evaluación de la propuesta '{self.target.title}' por {self.evaluator}"
        return f"Evaluación (sin objetivo) por {self.evaluator}"
    
    @property
    def target_object(self):
        """Helper to get the actual Expression or Proposal object."""
        return self.target
    
    # @property
    # def target(self):
    #     """Resolves GenericForeignKey safely."""
    #     content_type = self.target_content_type
    #     model_class = content_type.model_class()
    #     return model_class._default_manager.get(pk=self.target_object_id)

    @property
    def project_title(self):
        """Shortcut to access project_title regardless of target type."""
        return getattr(self.target, 'project_title', None)

    @property
    def call(self):
        """Shortcut to access call via target."""
        return getattr(self.target, 'call', None)

    @property
    def user(self):
        """Shortcut to access user via target."""
        return getattr(self.target, 'user', None)

class EvaluationResponse(models.Model):
    """
    Respuesta a un ítem de evaluación.
    Almacena la respuesta real del evaluador.
    """
    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name="Evaluación"
    )
    item = models.ForeignKey(
        TemplateItem,
        on_delete=models.PROTECT,
        verbose_name="Ítem Evaluado"
    )
    value = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Valor"
    )
    score = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name="Puntuación"
    )
    comment = models.TextField(
        blank=True,
        verbose_name="Comentario"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado")

    class Meta:
        unique_together = ('evaluation', 'item')
        verbose_name = "Respuesta de Evaluación"
        verbose_name_plural = "Respuestas de Evaluación"

    def __str__(self):
        return f"Respuesta: {self.score} por {self.evaluator}"

# class Evaluation(TimestampMixin, CreatedByMixin, models.Model):
#     """
#     Representa la evaluacion hecha por un revisor a 
#     una Expresion de Interes.
#     """
#     expression = models.ForeignKey(
#         'expressions.Expression',
#         on_delete=models.CASCADE,
#         verbose_name="Expresión de Interés"
#     )
#     evaluator = models.ForeignKey(
#         'accounts.CustomUser',
#         on_delete=models.PROTECT,
#         verbose_name="Evaluador"
#     )
#     status = models.ForeignKey(
#         'common.Status',
#         on_delete=models.PROTECT,
#         verbose_name="Estado"
#     )
#     total_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
#     max_possible_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
#     submission_datetime = models.DateTimeField(null=True, blank=True)

#     class Meta:
#         unique_together = ('expression', 'evaluator')
#         db_table = 'evaluation'
#         verbose_name = "Evaluación"
#         verbose_name_plural = "Evaluaciones"
#         ordering = ['-submission_datetime']

#     def __str__(self):
#         return f"Evaluación de {self.expression.project_title} por {self.evaluator}"
    
# class EvaluationCategory(models.Model):
#     evaluation = models.ForeignKey(
#         Evaluation, 
#         on_delete=models.CASCADE, 
#         related_name='categories',
#         verbose_name="Evaluación"
#     )
#     name = models.CharField(max_length=100, verbose_name="Nombre")
#     weight = models.DecimalField(max_digits=3, 
#         decimal_places=1, 
#         default=1.0,
#         verbose_name="Peso (%)"
#     )
#     order = models.PositiveIntegerField(default=0)

#     class Meta:
#         ordering = ['order']
#         verbose_name = "Categoría de Evaluación"
#         verbose_name_plural = "Categorías de Evaluación"

#     def __str__(self):
#         return self.name


# class EvaluationItem(models.Model):
#     category = models.ForeignKey(EvaluationCategory, on_delete=models.CASCADE, related_name='items', verbose_name="Categoría")
#     question = models.TextField(verbose_name="Pregunta")
#     max_score = models.DecimalField(max_digits=3, decimal_places=1, default=5.0, verbose_name="Puntuación Máxima")
#     help_text = models.TextField(blank=True, verbose_name="Texto de Ayuda")
#     order = models.PositiveIntegerField(default=0, verbose_name="Orden") 

#     class Meta:
#         ordering = ['order']
#         verbose_name = "Ítem de Evaluación"
#         verbose_name_plural = "Ítems de Evaluación"

#     def __str__(self):
#         return f"{self.category.name}: {self.question}"


# class EvaluationResponse(models.Model):
#     item = models.ForeignKey(EvaluationItem, on_delete=models.CASCADE, related_name='responses', verbose_name="Ítem Evaluado")
#     evaluator = models.ForeignKey('accounts.CustomUser', on_delete=models.PROTECT, verbose_name="Evaluador")
#     score = models.DecimalField(max_digits=3, decimal_places=1, verbose_name="Puntuación")
#     comment = models.TextField(blank=True, verbose_name="Comentario")
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado")
#     updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizado")

#     class Meta:
#         unique_together = ('item', 'evaluator')
#         verbose_name = "Respuesta de Evaluación"
#         verbose_name_plural = "Respuestas de Evaluación"

#     def __str__(self):
#         return f"Respuesta: {self.score} por {self.evaluator}"

# ===== From: common/models.py =====

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

# ===== From: accounts/models.py =====

#from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from django.db import models
from core.models import TimestampMixin, CreatedByMixin
from django.core.validators import RegexValidator

class Role(TimestampMixin, CreatedByMixin, models.Model):
    id = models.AutoField(
        primary_key=True,
        verbose_name="ID Rol"
    )
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


    # Link to Django Groups
    group = models.OneToOneField(
        'auth.Group',
        on_delete=models.PROTECT,
        verbose_name="Grupo de Permisos",
        help_text="Grupo de Permisos de Django asociado a este rol",
        null=True,
        blank=True
    )

    class Meta:
        db_table= 'role'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                #condition=models.Q(is_active=True),
                name='unique_active_role_name'
            )
        ]
    def __str__(self):
        return self.name

#class User(AbstractUser):
class CustomUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    person = models.OneToOneField(
        'people.Person',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_account'
    )

    role = models.ForeignKey(
        'accounts.Role',
        on_delete=models.PROTECT, # We keep the user even  if the role is deleted
        null=True,
        blank=True,
        related_name='users',
        verbose_name='Rol'
    )

    birthdate = models.DateField(
        verbose_name="Fecha de nacimiento",
        blank=True,
        null=True
    )

    email = models.EmailField(unique=True, verbose_name="Correo electronico")

    phone_number = models.CharField(
        max_length=17,
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]{9,17}$',
                message="Por favor, ingrese un numero de telefono valido (por ejemplo, +57(601)1234444, +1 555-123-4567 o (44) 20 7946 0958)."
            )
        ]
    )

    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='accounts_user_groups',
        related_query_name='accounts_user'
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        blank=True,
        related_name='accounts_user_permissions',
        related_query_name='acounts_user'
    )

    class Meta:
        db_table = 'accounts_user' # Customize talbe name

    def __str__(self):
        return f"{self.user.username} ({self.role.name if self.role else 'No Role'})"