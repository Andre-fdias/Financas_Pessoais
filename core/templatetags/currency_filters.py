from django import template
from django.template.defaultfilters import floatformat
from decimal import Decimal

register = template.Library()

@register.filter
def br_currency(value):
    """Formata valor como moeda brasileira (R$)"""
    try:
        if isinstance(value, (int, float, Decimal)):
            # Formata com 2 casas decimais, separador de milhar e decimal correto
            return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return value
    except (ValueError, TypeError):
        return value

@register.filter
def classname(obj):
    """Retorna o nome da classe do objeto"""
    return obj.__class__.__name__



@register.filter
def keys(dictionary):
    return list(dictionary.keys())

@register.filter
def values(dictionary):
    return list(dictionary.values())