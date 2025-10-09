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