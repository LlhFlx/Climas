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