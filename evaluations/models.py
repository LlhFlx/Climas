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