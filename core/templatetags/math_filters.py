from django import template

register = template.Library()

@register.filter
def div(value, arg):
    """Divide o value pelo arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiplica o value pelo arg"""
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def abs(value):
    """Valor absoluto"""
    try:
        return abs(float(value))
    except ValueError:
        return 0