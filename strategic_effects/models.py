from django.db import models
from core.models import TimestampMixin, CreatedByMixin
from thematic_axes.models import ThematicAxis

class StrategicEffect(TimestampMixin, CreatedByMixin, models.Model):
    """
    Efecto estrategico predefinido en la documentacion.
    """
    name = models.CharField(
        max_length=500,
        unique=True,
        verbose_name="Nombre"
    )

    description = models.TextField(
        blank=True, 
        verbose_name="Descripcion"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    thematic_axis = models.ForeignKey(
        'thematic_axes.ThematicAxis',
        on_delete=models.PROTECT,
        verbose_name="Eje Temático",
        help_text="Eje temático al que pertenece este efecto estratégico"
    )

    class Meta:
        db_table = 'strategic_effect'
        verbose_name="Efecto Estrategico"
        verbose_name_plural="Efectos Estrategicos"
        ordering = ['thematic_axis__name', 'name']

    def __str__(self):
        return self.name
    

# LOAD VIA FIXTURES (TEMPLATE)

# [
#   {
#     "model": "common.strategiceffect",
#     "fields": {
#       "name": "Desarrollo Económico Local",
#       "description": "Impulso a la economía en comunidades vulnerables."
#     }
#   },
#   {
#     "model": "common.strategiceffect",
#     "fields": {
#       "name": "Innovación Tecnológica",
#       "description": "Generación de nuevas tecnologías o procesos."
#     }
#   }
# ]