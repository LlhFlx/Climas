from django.db import models
from django.apps import apps
from core.models import TimestampMixin, CreatedByMixin
from core.choices import FIELD_TYPE_CHOICES, SOURCE_MODEL_CHOICES
from expressions.models import Expression
from accounts.models import User
from common.models import Status


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

    class Meta:
        db_table = 'evaluation_template'
        verbose_name = "Plantilla de Evaluacion"
        verbose_name_plural = "Plantillas de Evaluacion"
        ordering = ['name']

    def __str__(self):
        return self.name


class TemplateCategory(TimestampMixin, models.Model):
    template = models.ForeignKey(
        EvaluationTemplate,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name="Plantilla"
    )

    name = models.CharField(
        max_length=100, 
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
    
class TemplateItem(TimestampMixin, models.Model):
    """
    Ítem de evaluación (pregunta) dentro de una categoría.
    Define el tipo de entrada esperado.
    """

    # FIELD_TYPE_CHOICES = [
    #     ('text', 'Texto largo'),
    #     ('short_text', 'Texto corto'),
    #     ('number', 'Número'),
    #     ('boolean', 'Sí/No'),
    #     ('dropdown', 'Desplegable'),
    #     ('radio', 'Opción múltiple'),
    # ]

    # SOURCE_MODEL_CHOICES = [
    #     ('geo.Country', 'Pais'),
    #     ('common.Status', 'Estado'),
    #     ('thematic_axes.ThematicAxis', 'Eje Tematico')
    # ]

    category = models.ForeignKey(
        TemplateCategory,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Categoría"
    )

    question = models.TextField(verbose_name="Pregunta")

    field_type = models.CharField(
        max_length=20,
        choices=FIELD_TYPE_CHOICES,
        default='text',
        verbose_name="Tipo de Campo"
    )
    # Static Options
    options = models.JSONField(
        blank=True,
        null=True,
        help_text="Opciones para dropdown o radio (ej: ['Sí', 'No', 'Parcialmente'])",
        verbose_name="Opciones Estaticas"
    )

    # Dynamic model reference
    source_model = models.CharField(
        max_length=100,
        choices=SOURCE_MODEL_CHOICES,
        blank=True,
        null=True,
        help_text="Si se selecciona, carga opciones desde este modelo. (Ignorar para 'Opciones Estaticas')",
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
        return f"{self.category.name}: {self.question}"
    
    # def get_options(self):
    #     """
    #     Retorna una lista de opciones para este item.
    #     Prioriza 'source_model' sobre 'opciones'.
    #     """
    #     if self.source_model:
    #         try:
    #             app_label, model_name = self.source_model.split('.')
    #             model = apps.get_model(app_label, model_name)
    #             return list(model.objects.values_list('name', flat=True))
    #         except (LookupError, AttributeError) as e:
    #             return [f"Error loading {self.source_model}: {e}"]
    #     elif self.options:
    #         return self.options
    #     return []
    
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


class Evaluation(TimestampMixin, CreatedByMixin, models.Model):
    """
    Representa la evaluacion hecha por un revisor a 
    una Expresion de Interes.
    """
    expression = models.ForeignKey(
        'expressions.Expression',
        on_delete=models.CASCADE,
        verbose_name="Expresión de Interés"
    )
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

    class Meta:
        unique_together = ('expression', 'evaluator')
        db_table = 'evaluation'
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        ordering = ['-submission_datetime']

    def __str__(self):
        return f"Evaluación de {self.expression.project_title} por {self.evaluator}"

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