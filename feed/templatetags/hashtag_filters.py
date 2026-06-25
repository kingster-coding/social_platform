"""
WHAT: Custom template filters for hashtags
WHY: Automatically convert #hashtags to clickable links
"""

import re

from django import template
from django.urls import reverse
from django.utils.html import conditional_escape, format_html

register = template.Library()


@register.filter(name='hashtag_links')
@template.defaultfilters.stringfilter
def hashtag_links(value):
    """
    Convert #hashtags in text to clickable links.
    """
    if not value:
        return value

    escaped_value = conditional_escape(value)

    def replace_hashtag(match):
        tag = match.group(1)
        url = reverse('feed:hashtag', args=[tag.lower()])
        return format_html(
            '<a href="{}" style="color: var(--accent-color); text-decoration: none;">#{}</a>',
            url,
            tag,
        )

    return re.sub(r'#(\w+)', replace_hashtag, escaped_value)
