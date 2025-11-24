from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Get item from dictionary
    Usage: {{ mydict|get_item:key }}
    """
    if dictionary:
        return dictionary.get(key)
    return None