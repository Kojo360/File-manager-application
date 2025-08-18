from django import template
import os
from datetime import datetime

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

@register.filter
def get_file_extension(filename):
    """Get file extension"""
    if filename:
        return os.path.splitext(filename)[1].lower()
    return ''

@register.filter
def timestamp_to_date(timestamp):
    """Convert timestamp to datetime object"""
    try:
        return datetime.fromtimestamp(timestamp)
    except (ValueError, TypeError):
        return None
