from django.db import models

class Country(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(verbose_name="Nombre Pais", max_length=100, unique=True)
    phone_number_indicative = models.CharField(verbose_name="Indicativo", max_length=6)


    class Meta:
        db_table = 'country'
        verbose_name = "Pais"
        verbose_name_plural = "Paises"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.phone_number_indicative})"
    
class DocumentType(models.Model):
    id = models.AutoField(primary_key=True)
    country = models.ForeignKey(
        'geo.Country',
        on_delete=models.CASCADE,
        db_column='country_id',
        related_name='document_types',
        verbose_name='Paises'
    )
    
    name = models.CharField("Nombre de Tipo de Documento", max_length=100)

    class Meta:
        db_table = 'document_type'
        verbose_name = "Tipo Documento"
        verbose_name_plural = "Tipos Documento"
        unique_together = ('country', 'name')
        ordering = ['country', 'name']

def __str__(self):
    return f"{self.name} ({self.country.name})"