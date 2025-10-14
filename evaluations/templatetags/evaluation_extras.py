from django import template

register = template.Library()

@register.filter
def status_in(value, arg):
    """
    Check if value is in comma-separated string.
    Usage: {{ status.name|status_in:"Pendiente,En Progreso" }}
    """
    if not value or not arg:
        return False
    allowed_statuses = [s.strip() for s in arg.split(',')]
    return value in allowed_statuses