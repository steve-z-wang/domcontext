"""Pass 2: Filter by attributes - remove non-semantic attributes and nodes."""

from typing import Optional, Set
from ...ir.semantic_ir import SemanticTreeNode, SemanticElement, SemanticText

# Semantic attributes to preserve
SEMANTIC_ATTRIBUTES: Set[str] = {
    'role', 'aria-label', 'aria-labelledby', 'aria-describedby',
    'aria-checked', 'aria-selected', 'aria-expanded',
    'type', 'name', 'placeholder', 'value', 'alt', 'title'
}

# Non-semantic roles to filter out
NON_SEMANTIC_ROLES: Set[str] = {'none', 'presentation'}


def filter_by_attributes_pass(semantic_tree_node: SemanticTreeNode) -> Optional[SemanticTreeNode]:
    """
    Pass 2: Filter attributes to keep only semantic ones.

    - Keep only SEMANTIC_ATTRIBUTES (role, aria-label, type, name, etc.)
    - Remove non-semantic attributes

    Note: Does NOT filter out nodes. Visibility filtering already handled that.

    Args:
        semantic_tree_node: SemanticTreeNode to process

    Returns:
        SemanticTreeNode with filtered attributes, or None if empty
    """
    # Handle text nodes
    if isinstance(semantic_tree_node.data, SemanticText):
        # Keep text nodes with content
        if semantic_tree_node.data.text.strip():
            return semantic_tree_node
        else:
            return None

    # Handle element nodes
    semantic_element = semantic_tree_node.data

    # Filter attributes to keep only semantic ones
    filtered_attrs = {
        key: value
        for key, value in semantic_element.semantic_attributes.items()
        if key in SEMANTIC_ATTRIBUTES
    }

    # Create new SemanticElement with filtered attributes
    new_semantic_element = SemanticElement(
        tag=semantic_element.tag,
        semantic_attributes=filtered_attrs,
        dom_tree_node=semantic_element.dom_tree_node  # Preserve reference
    )

    # Create new SemanticTreeNode
    new_semantic_tree_node = SemanticTreeNode(data=new_semantic_element)

    # Process children recursively
    for child_semantic_tree_node in semantic_tree_node.children:
        filtered_child = filter_by_attributes_pass(child_semantic_tree_node)
        if filtered_child:
            new_semantic_tree_node.add_child(filtered_child)

    return new_semantic_tree_node
