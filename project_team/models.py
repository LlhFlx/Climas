from django.db import models
from core.models import TimestampMixin
# from expressions.models import Expression
# from people.models import Person
# from common.models import Status
# from thematic_axes.models import ThematicAxis


class ProjectTeamMember(TimestampMixin, models.Model):
    """
    Miembro del equipo de proyecto asignado a una Expresión de Interés.
    Define su rol, fechas y estado.
    """
    expression = models.ForeignKey(
        'expressions.Expression',
        on_delete=models.CASCADE,
        verbose_name="Expresión de Interés"
    )
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
    start_date = models.DateField(verbose_name="Fecha de Inicio")
    end_date = models.DateField(verbose_name="Fecha de Finalización")

    class Meta:
        db_table = 'project_team_member'
        verbose_name = "Miembro del Equipo de Proyecto"
        verbose_name_plural = "Miembros del Equipo de Proyecto"
        unique_together = ('expression', 'person')
        ordering = ['expression', 'role']

    def __str__(self):
        return f"{self.person} - {self.role} ({self.institution.name if self.institution else 'Sin Institución'})"


class InvestigatorThematicAxisAntecedent(TimestampMixin, models.Model):
    """
    Antecedente del investigador en un eje temático específico.
    """
    team_member = models.ForeignKey(
        'project_team.ProjectTeamMember',
        on_delete=models.CASCADE,
        related_name='thematic_antecedents',
        verbose_name="Miembro del Equipo"
    )
    thematic_axis = models.ForeignKey(
        'thematic_axes.ThematicAxis',
        on_delete=models.PROTECT,
        verbose_name="Eje Temático"
    )
    description = models.TextField(verbose_name="Descripción del Antecedente")
    evidence_url = models.URLField(
        blank=True,
        verbose_name="URL de Evidencia"
    )

    class Meta:
        db_table = 'investigator_thematic_antecedent'
        verbose_name = "Antecedente en Eje Temático"
        verbose_name_plural = "Antecedentes en Ejes Temáticos"

    def __str__(self):
        return f"{self.team_member.person} - {self.thematic_axis}"


class InvestigatorCondition(TimestampMixin, models.Model):
    """
    Condición específica de participación del investigador.
    """
    team_member = models.ForeignKey(
        'project_team.ProjectTeamMember',
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