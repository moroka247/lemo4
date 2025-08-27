from django import template

register = template.Library()

@register.filter
def percent(value, decimals=4):
    """Convert a number to a percentage string with specified decimal places."""
    try:
        value = float(value)  # Convert Decimal to float
        return f"{value * 100:.{decimals}f}%"
    except (TypeError, ValueError):
        return ''

@register.filter
def div(value, arg):
    """Safely divide two numbers."""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.filter
def get_value(dictionary, key):
    """Safely get a value from a dictionary (default: empty string)."""
    return dictionary.get(key, "")

@register.filter
def get_item(dictionary, key):
    """Safely get a value from a dictionary (default: 0)."""
    return dictionary.get(key, 0) if isinstance(dictionary, dict) else 0

@register.filter
def negate(value):
    """Multiplies a number by -1 but keeps zero as zero"""
    try:
        value = float(value)  # Convert to float
        if value == 0:
            return 0  # Prevent -0 from appearing
        return value * -1
    except (ValueError, TypeError):
        return value  # Return original value if conversion fails

@register.filter
def bracket_negative(value):
    try:
        value = float(value)  # Ensure it's a number
        if value < 0:
            return f"({abs(value):,.2f})"  # Format with commas and 2 decimal places
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return value  # Return as-is if it's not a number

@register.filter
def subtract(value, arg):
    return value - arg

@register.filter
def divide(value, arg):
    if arg == 0:
        return 0
    return value / arg

@register.filter
def multiply(value, arg):
    return value * arg


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def first_investor(queryset, investor_id):
    for item in queryset:
        if item.investor.id == int(investor_id):
            return item.investor
    return None

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)