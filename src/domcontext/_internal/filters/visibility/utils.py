"""Shared utilities for visibility filtering."""

from typing import Set

# Tags that are not visible/rendered (not part of visible DOM)
NON_VISIBLE_TAGS: Set[str] = {
    'script',    # JavaScript code
    'style',     # CSS styles
    'head',      # Document metadata container
    'meta',      # Metadata
    'link',      # External resources
    'title',     # Document title (in head)
    'noscript',  # No-script content
}


def parse_inline_style(style_attr: str) -> dict:
    """
    Parse inline style attribute into a dictionary.

    Args:
        style_attr: Style attribute string like "display:none;color:red"

    Returns:
        Dictionary of style properties
    """
    styles = {}
    if not style_attr:
        return styles

    # Split by semicolon
    for declaration in style_attr.split(';'):
        declaration = declaration.strip()
        if ':' in declaration:
            prop, value = declaration.split(':', 1)
            styles[prop.strip().lower()] = value.strip().lower()

    return styles
