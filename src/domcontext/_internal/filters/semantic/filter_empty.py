"""Pass 3: Filter empty nodes - remove nodes with no attributes and no children."""

from typing import Optional, Set
from ...ir.semantic_ir import SemanticTreeNode, SemanticElement, SemanticText

# Interactive tags that should be kept even without attributes
INTERACTIVE_TAGS: Set[str] = {
    'a', 'button', 'input', 'select', 'textarea', 'label'
}


def filter_empty_nodes_pass(semantic_tree_node: SemanticTreeNode) -> Optional[SemanticTreeNode]:
    """
    Pass 3: Filter empty nodes.

    Remove nodes that have:
    - No semantic attributes AND
    - No children

    Exception: Keep interactive tags even without attributes (they may be useful)

    Args:
        semantic_tree_node: SemanticTreeNode to process

    Returns:
        SemanticTreeNode, or None if empty
    """
    # Handle text nodes
    if isinstance(semantic_tree_node.data, SemanticText):
        # Keep text with content
        if semantic_tree_node.data.text.strip():
            return semantic_tree_node
        else:
            return None

    # Handle element nodes
    semantic_element = semantic_tree_node.data

    # Process children first (bottom-up)
    filtered_children = []
    for child_semantic_tree_node in semantic_tree_node.children:
        filtered_child = filter_empty_nodes_pass(child_semantic_tree_node)
        if filtered_child:
            filtered_children.append(filtered_child)

    # Check if node should be filtered
    has_attributes = bool(semantic_element.semantic_attributes)
    has_children = bool(filtered_children)
    is_interactive = semantic_element.tag in INTERACTIVE_TAGS

    # Filter out if: no attributes AND no children AND not interactive
    if not has_attributes and not has_children and not is_interactive:
        return None

    # Keep node - create new SemanticElement and SemanticTreeNode
    new_semantic_element = SemanticElement(
        tag=semantic_element.tag,
        semantic_attributes=semantic_element.semantic_attributes.copy(),
        dom_tree_node=semantic_element.dom_tree_node  # Preserve reference
    )

    new_semantic_tree_node = SemanticTreeNode(data=new_semantic_element)

    for child in filtered_children:
        new_semantic_tree_node.add_child(child)

    return new_semantic_tree_node
