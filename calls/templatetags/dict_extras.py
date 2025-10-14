# calls/templatetags/dict_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')

@register.filter
def add(value, arg):
    return str(value) + str(arg)

@register.filter
def contains(value, item):
    """Check if item is in list."""
    return item in value