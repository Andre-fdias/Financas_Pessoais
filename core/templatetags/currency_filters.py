# core/templatetags/currency_filters.py

from django import template
from decimal import Decimal
import locale # Importe o módulo locale

register = template.Library()

@register.filter
def br_currency(value):
    """
    Formata um valor numérico para o formato de moeda brasileiro (R$ X.XXX,XX).
    Utiliza o módulo locale para uma formatação mais robusta.
    """
    if value is None:
        return "R$ 0,00" # Retorna um valor padrão para None

    try:
        # Garante que o valor é Decimal para evitar problemas de float
        value = Decimal(str(value))
        
        # Tenta definir o locale para português do Brasil
        # Pode precisar de 'pt_BR.UTF-8' ou 'pt_BR' dependendo do seu sistema operacional
        try:
            locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'pt_BR')
            except locale.Error:
                # Se nenhum dos locales específicos funcionar, use um fallback mais genérico
                # e registe um aviso (em um ambiente real, usaria logging)
                print("Aviso: Não foi possível definir o locale 'pt_BR.UTF-8' ou 'pt_BR'.")
                # Fallback para formatação manual se locale falhar
                return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


        # Formata o número como moeda utilizando o locale definido
        # grouping=True garante o separador de milhares
        # symbol=True inclui o símbolo da moeda (R$)
        return locale.currency(value, grouping=True, symbol=True)

    except (ValueError, TypeError) as e:
        # Se ocorrer um erro de conversão ou tipo, loga o erro e retorna o valor original
        print(f"Erro ao formatar moeda '{value}': {e}")
        return value # Retorna o valor original não formatado em caso de erro

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
