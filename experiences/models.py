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