from django import template

register = template.Library()

@register.filter
def status_color(status):
    """Return Bootstrap color class for status"""
    color_map = {
        'uploaded': 'info',
        'fully_indexed': 'success',
        'partially_indexed': 'warning',
        'failed': 'danger'
    }
    return color_map.get(status, 'secondary')
