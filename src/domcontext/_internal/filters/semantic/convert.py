"""Pass 0: Convert DomTreeNode → SemanticTreeNode.

This is a pure conversion step with no filtering logic.
"""

from ...ir.dom_ir import DomTreeNode, DomElement, DomText
from ...ir.semantic_ir import SemanticTreeNode, SemanticElement, SemanticText


def convert_to_semantic_pass(dom_tree_node: DomTreeNode) -> SemanticTreeNode:
    """
    Pass 0: Convert DomTreeNode → SemanticTreeNode.

    Pure conversion - no filtering, just creates SemanticTreeNode structure
    with references back to DomTreeNode.

    Args:
        dom_tree_node: DomTreeNode to convert

    Returns:
        SemanticTreeNode with reference to DomTreeNode
    """
    # Handle text nodes
    if isinstance(dom_tree_node.data, DomText):
        # Create SemanticText with reference to DomTreeNode
        semantic_text = SemanticText(
            text=dom_tree_node.data.text,
            dom_tree_node=dom_tree_node
        )
        return SemanticTreeNode(data=semantic_text)

    # Handle element nodes
    dom_element = dom_tree_node.data

    # Create SemanticElement with reference to DomTreeNode
    semantic_element = SemanticElement(
        tag=dom_element.tag,
        semantic_attributes=dom_element.attributes.copy(),  # Will be filtered in later passes
        dom_tree_node=dom_tree_node
    )

    # Create SemanticTreeNode wrapping the SemanticElement
    semantic_tree_node = SemanticTreeNode(data=semantic_element)

    # Process children recursively
    for child_dom_tree_node in dom_tree_node.children:
        semantic_child = convert_to_semantic_pass(child_dom_tree_node)
        semantic_tree_node.add_child(semantic_child)

    return semantic_tree_node
