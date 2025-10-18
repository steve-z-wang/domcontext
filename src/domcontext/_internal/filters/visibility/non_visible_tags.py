"""Pass 1: Remove non-visible tags (script, style, head, etc.)."""

from typing import Optional
from ...ir.dom_ir import DomTreeNode, DomElement, DomText
from .utils import NON_VISIBLE_TAGS


def filter_non_visible_tags_pass(tree_node: DomTreeNode) -> Optional[DomTreeNode]:
    """
    Pass 1: Remove non-visible tags (script, style, head, etc.).

    Args:
        tree_node: DomTreeNode to filter

    Returns:
        New DomTreeNode, or None if this node is non-visible tag
    """
    # Keep text nodes
    if isinstance(tree_node.data, DomText):
        new_node = DomTreeNode(data=tree_node.data)
        return new_node

    element = tree_node.data

    # Filter out non-visible tags
    if element.tag in NON_VISIBLE_TAGS:
        return None

    # Keep this node, process children
    new_node = DomTreeNode(data=element)
    for child in tree_node.children:
        filtered_child = filter_non_visible_tags_pass(child)
        if filtered_child:
            new_node.add_child(filtered_child)

    return new_node
