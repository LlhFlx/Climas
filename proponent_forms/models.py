from django.apps import apps
from django.db import models
from core.models import TimestampMixin
from core.choices import SOURCE_MODEL_CHOICES, FIELD_TYPE_CHOICES

class SharedQuestion(TimestampMixin, models.Model):
    TARGET_CHOICES = [
        ('expression', 'Expresion de Interes'),
        ('proposal', 'Propuesta Completa')
    ]

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
        ordering = ['target_category', 'question']

    def __str__(self):
        return f"{self.question} ({self.get_target_category_display()})"
    
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
