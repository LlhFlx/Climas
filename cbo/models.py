from django.db import models
from core.models import TimestampMixin
import os

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
        

class CBODocument(TimestampMixin, models.Model):
    """
    Document associated with a CBO (e.g., legal registration, proof of operation).
    """
    cbo = models.ForeignKey(
        'cbo.CBO',
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="CBO"
    )
    file = models.FileField(
        upload_to='cbo_documents/%Y/%m/%d/',
        verbose_name="Archivo",
        help_text="Suba documentos como acta de constitución, RUT, etc. Máximo 10MB."
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
        db_table = 'cbo_document'
        verbose_name = "Documento de CBO"
        verbose_name_plural = "Documentos de CBO"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name or self.file.name} ({self.cbo.name})"

    def save(self, *args, **kwargs):
        if not self.name and self.file:
            self.name = os.path.basename(self.file.name)
        super().save(*args, **kwargs)