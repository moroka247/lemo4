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

@register.simple_tag
def total_investor_amount(descriptions, investor_id):
    """Calculate total amount for a specific investor across all descriptions"""
    total = 0
    for desc_data in descriptions.values():
        amount = desc_data['investor_amounts'].get(investor_id, 0)
        if amount:
            total += amount
    return f"{total:,.2f}" if total != 0 else "-"

@register.filter(name='sub')
def sub(value, arg):
    """Subtract the arg from the value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='div')
def div(value, arg):
    """Divide value by arg"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_field(form, field_name):
    """Get form field by name"""
    return form[field_name]

@register.filter
def add(str1, str2):
    """Concatenate two strings"""
    return str(str1) + str(str2)

@register.filter
def get_field(form, field_name):
    """Get form field by name, returns None if field doesn't exist"""
    try:
        return form[field_name]
    except KeyError:
        return None

@register.filter
def get_field_or_empty(form, field_name):
    """Get form field by name, returns empty string if field doesn't exist (for safe rendering)"""
    try:
        return form[field_name]
    except KeyError:
        return ""

@register.filter
def get_field_by_index(form, base_name, index):
    """Get form field by base name and index"""
    field_name = f"{base_name}{index}_end_month"
    try:
        return form[field_name]
    except KeyError:
        return None