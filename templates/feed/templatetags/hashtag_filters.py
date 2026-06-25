"""
WHAT: Custom template filters for hashtags
WHY: Automatically convert #hashtags to clickable links
"""

import re
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name='hashtag_links')
def hashtag_links(value):
    """
    Convert #hashtags in text to clickable links
    """
    if not value:
        return value
    
    def replace_hashtag(match):
        tag = match.group(1)
        url = f'/hashtag/{tag.lower()}/'
        return f'<a href="{url}" style="color: var(--accent-color); text-decoration: none;">#{tag}</a>'
    
    pattern = r'#(\w+)'
    result = re.sub(pattern, replace_hashtag, value)
    
    return mark_safe(result)