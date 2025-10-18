"""Pass 4: Collapse wrappers - collapse single-child wrappers with no attributes."""

from typing import Optional
from ...ir.semantic_ir import SemanticTreeNode, SemanticElement, SemanticText


def collapse_wrappers_pass(semantic_tree_node: SemanticTreeNode) -> Optional[SemanticTreeNode]:
    """
    Pass 4: Collapse single-child wrappers with no attributes.

    If a node has:
    - No attributes AND
    - Exactly one element child (ignoring whitespace text)
    → Promote the child (collapse wrapper)

    Args:
        semantic_tree_node: SemanticTreeNode to process

    Returns:
        SemanticTreeNode or promoted child, or None
    """
    # Handle text nodes
    if isinstance(semantic_tree_node.data, SemanticText):
        return semantic_tree_node

    # Handle element nodes
    semantic_element = semantic_tree_node.data

    # Process children first (bottom-up)
    collapsed_children = []
    for child_semantic_tree_node in semantic_tree_node.children:
        collapsed_child = collapse_wrappers_pass(child_semantic_tree_node)
        if collapsed_child:
            collapsed_children.append(collapsed_child)

    # Check if this is a wrapper to collapse
    has_attributes = bool(semantic_element.semantic_attributes)

    if not has_attributes:
        # Count element children and meaningful text
        element_children = [c for c in collapsed_children if isinstance(c.data, SemanticElement)]
        text_children = [c for c in collapsed_children if isinstance(c.data, SemanticText)]
        has_meaningful_text = any(c.data.text.strip() for c in text_children)

        # Collapse if: no attributes, single element child, no meaningful text
        if len(element_children) == 1 and not has_meaningful_text:
            # Promote the child
            return element_children[0]

    # Keep node - create new SemanticElement and SemanticTreeNode
    new_semantic_element = SemanticElement(
        tag=semantic_element.tag,
        semantic_attributes=semantic_element.semantic_attributes.copy(),
        dom_tree_node=semantic_element.dom_tree_node  # Preserve reference
    )

    new_semantic_tree_node = SemanticTreeNode(data=new_semantic_element)

    for child in collapsed_children:
        new_semantic_tree_node.add_child(child)

    return new_semantic_tree_node
