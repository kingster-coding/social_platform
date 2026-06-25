"""
WHAT: Shared hashtag utilities for feed and reels
WHY: Keep hashtag extraction, matching, and counting consistent across apps
"""

import re

from django.db.models import Q

HASHTAG_PATTERN = re.compile(r'(?<!\w)#(?P<tag>\w+)')


# WHAT: Return normalized hashtag names from user text.
def extract_normalized_hashtags(text, max_tags=10):
    """
    Return lowercase unique hashtag names while preserving order.
    """
    if not text:
        return []

    hashtag_names = []
    seen_tags = set()

    for match in HASHTAG_PATTERN.finditer(text):
        normalized_tag = match.group('tag').lower()
        if normalized_tag in seen_tags:
            continue

        seen_tags.add(normalized_tag)
        hashtag_names.append(normalized_tag)

        if len(hashtag_names) >= max_tags:
            break

    return hashtag_names


# WHAT: Build an exact hashtag regex filter for a text field.
def build_hashtag_lookup(field_name, hashtag_name):
    """
    Match exact hashtags like #python without matching #python3 when searching #python.
    """
    escaped_tag = re.escape(hashtag_name.lower())
    hashtag_regex = rf'(^|[^0-9A-Za-z_])#{escaped_tag}([^0-9A-Za-z_]|$)'
    return Q(**{f'{field_name}__iregex': hashtag_regex})
