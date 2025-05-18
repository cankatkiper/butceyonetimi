from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Bir sözlükteki belirli bir anahtarın değerini döndüren filtre.
    Örnek kullanım: {{ mydict|get_item:key }}
    """
    return dictionary.get(key, 0)

@register.filter
def split(value, delimiter=','):
    """
    Bir stringi belirtilen ayırıcıya göre bölen filtre.
    Örnek kullanım: {{ "a,b,c"|split:"," }}
    """
    return value.split(delimiter)

@register.filter
def multiply(value, arg):
    """
    Bir değeri verilen sayı ile çarpan filtre.
    Örnek kullanım: {{ value|multiply:2 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0 