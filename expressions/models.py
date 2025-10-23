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
        related_name='expressions'  
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