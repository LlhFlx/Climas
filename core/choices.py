from django.utils.translation import gettext_lazy as _

# ---------------------------
# Field Type Choices
# ---------------------------

FIELD_TYPE_CHOICES = [
    ('text', 'Texto largo'),
    ('short_text', 'Texto corto'),
    ('number', 'Número'),
    ('boolean', 'Sí/No'),
    ('dropdown', 'Desplegable (Opciones Estáticas)'),
    ('dynamic_dropdown', 'Desplegable (Opciones Dinámicas)'),
    ('radio', 'Opción múltiple'),
]

# ---------------------------
# Source Model Choices
# ---------------------------
SOURCE_MODEL_CHOICES = [
    ('geo.Country', _('País')),
    ('common.Status', _('Estado')),
    ('thematic_axes.ThematicAxis', _('Eje Temático')),
    ('budgets.BudgetPeriod', _('Período de Presupuesto')),
    ('budgets.BudgetCategory', _('Categoría de Presupuesto')),
    ('institutions.Institution', _('Institución')),
    ('intersectionality.IntersectionalityScope', _('Ámbito de Interseccionalidad')),
    ('people.Person', _('Persona')),
    ('strategic_effects.StrategicEffect', _('Efecto Estratégico')),
]