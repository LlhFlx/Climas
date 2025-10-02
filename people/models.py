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
