from django.db import models
from django.contrib.auth.models import User

class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha Creacion', db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha Actualizacion')

    class Meta:
        abstract = True

class AddressMixin(models.Model):
    address_line1 = models.CharField(max_length=255, blank=True, verbose_name="Address Line 1")
    address_line2 = models.CharField(max_length=255, blank=True, verbose_name="Address Line 2")
    city = models.CharField(max_length=100, blank=True, verbose_name="Ciudad")
    state = models.CharField(max_length=100, blank=True, verbose_name="Departamento/Provincia")
    # country = models.CharField(max_length=100, blank=True, verbose_name="Pais")

    class Meta:
        abstract=True

class CreatedByMixin(models.Model):
    created_by = models.ForeignKey(
        # 'accounts.CustomUser',
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_index=True,
        related_name="%(app_label)s_%(class)s_created"
    )
    
    class Meta:
        abstract=True


