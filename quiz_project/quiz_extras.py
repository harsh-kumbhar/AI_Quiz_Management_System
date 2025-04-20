import re
from django import template

register = template.Library()

def my_custom_filter(value):
    return value.upper()

@register.filter
def normalize_option(value):
    """Remove option labels like A), B., C: and return the core text."""
    if not value:
        return ''
    value = value.lower().strip()
    value = re.sub(r'^[a-d][\)\.\:\s]+', '', value)
    return value.strip()
