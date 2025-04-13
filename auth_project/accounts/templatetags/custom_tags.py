from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Bir sözlükteki belirli bir anahtarın değerini döndüren filtre.
    Örnek kullanım: {{ mydict|get_item:key }}
    """
    return dictionary.get(key, 0) 