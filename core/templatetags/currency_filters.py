from django import template
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def br_currency(value):
    """Formata valor como moeda brasileira (R$)"""
    try:
        value = float(value)
        # Formata com 2 casas decimais, separador de milhar e decimal correto
        return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return value