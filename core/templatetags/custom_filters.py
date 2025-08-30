from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        # Se for um dicionário, usa o método get()
        return dictionary.get(key)
    elif isinstance(dictionary, list):
        # Se for uma lista de tuplas, itera sobre ela
        for k, v in dictionary:
            if str(k) == str(key):
                return v
    return '' # Retorna uma string vazia se não encontrar ou se não for um tipo suportado


@register.filter
def abs(value):
    """Retorna o valor absoluto de um número"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter
def direction_arrow(value):
    """Retorna uma seta para cima ou para baixo baseado no valor"""
    try:
        if float(value) >= 0:
            return "↑"  # Seta para cima
        else:
            return "↓"  # Seta para baixo
    except (ValueError, TypeError):
        return ""