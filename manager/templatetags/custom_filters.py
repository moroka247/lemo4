from django import template

register = template.Library()

@register.filter
def percent(value, decimals=4):
    try:
        # Convert value to a percentage format with specified decimal places
        return f"{value * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return ''
    
@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])
