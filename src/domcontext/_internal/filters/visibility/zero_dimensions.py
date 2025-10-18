"""Pass 3: Remove zero-dimension elements without visible children."""

from typing import Optional
from ...ir.dom_ir import DomTreeNode, DomElement, DomText


def filter_zero_dimensions_pass(tree_node: DomTreeNode) -> Optional[DomTreeNode]:
    """
    Pass 3: Remove zero-dimension elements that have no visible children.

    This pass allows zero-dimension CONTAINERS if they have children with
    real dimensions (e.g., absolutely positioned popup dialogs).

    Args:
        tree_node: DomTreeNode to filter

    Returns:
        New DomTreeNode, or None if zero-dimension with no visible children
    """
    # Keep text nodes
    if isinstance(tree_node.data, DomText):
        new_node = DomTreeNode(data=tree_node.data)
        return new_node

    element = tree_node.data

    # Process children FIRST (bottom-up approach)
    new_node = DomTreeNode(data=element)
    for child in tree_node.children:
        filtered_child = filter_zero_dimensions_pass(child)
        if filtered_child:
            new_node.add_child(filtered_child)

    # Check if this element has zero dimensions
    has_zero_dimensions = False
    if element.bounds:
        if element.bounds.width <= 0 or element.bounds.height <= 0:
            has_zero_dimensions = True

    # If zero dimensions and NO children, filter it out
    # But if it has children, keep it (it's a container for positioned elements)
    if has_zero_dimensions and len(new_node.children) == 0:
        return None

    return new_node
