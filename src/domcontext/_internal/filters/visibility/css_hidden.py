"""Pass 2: Remove CSS-hidden elements (display:none, visibility:hidden, opacity:0)."""

from typing import Optional
from ...ir.dom_ir import DomTreeNode, DomElement, DomText
from .utils import parse_inline_style


def filter_css_hidden_pass(tree_node: DomTreeNode) -> Optional[DomTreeNode]:
    """
    Pass 2: Remove CSS-hidden elements (display:none, visibility:hidden, opacity:0).

    Args:
        tree_node: DomTreeNode to filter

    Returns:
        New DomTreeNode, or None if CSS-hidden
    """
    # Keep text nodes
    if isinstance(tree_node.data, DomText):
        new_node = DomTreeNode(data=tree_node.data)
        return new_node

    element = tree_node.data

    # Check CSS styles
    display = element.styles.get('display', '').lower()
    visibility = element.styles.get('visibility', '').lower()
    opacity = element.styles.get('opacity', '1')

    # Check inline style attribute (takes precedence)
    inline_style = element.attributes.get('style', '')
    if inline_style:
        inline_styles = parse_inline_style(inline_style)
        display = inline_styles.get('display', display)
        visibility = inline_styles.get('visibility', visibility)
        opacity = inline_styles.get('opacity', opacity)

    # Filter CSS-hidden elements
    if display == 'none':
        return None
    if visibility == 'hidden':
        return None
    try:
        if float(opacity) == 0:
            return None
    except (ValueError, TypeError):
        pass

    # Check hidden attribute
    if 'hidden' in element.attributes:
        return None

    # Check for hidden input
    if element.tag == 'input' and element.attributes.get('type', '').lower() == 'hidden':
        return None

    # Keep this node, process children
    new_node = DomTreeNode(data=element)
    for child in tree_node.children:
        filtered_child = filter_css_hidden_pass(child)
        if filtered_child:
            new_node.add_child(filtered_child)

    return new_node
