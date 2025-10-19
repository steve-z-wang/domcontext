"""Semantic processing for domnode trees.

Adds semantic IDs and preserves original node references during filtering.
"""

from typing import Dict, Optional, Tuple

from domnode import Node, Text, filter_visible, filter_semantic
from domnode.filters.semantic import (
    filter_attributes,
    filter_empty,
    filter_presentational_roles,
    collapse_single_child_wrappers,
)


def deep_copy_with_metadata(node: Node, original: Optional[Node] = None) -> Node:
    """Deep copy a node tree, preserving metadata and original node reference.

    Args:
        node: Node to copy
        original: Original node to reference (if this is a filtered copy)

    Returns:
        Deep copy of node with original_node in metadata
    """
    # Create new node with same data
    new_node = Node(
        tag=node.tag,
        attrib=dict(node.attrib),
        styles=dict(node.styles),
        bounds=node.bounds,
        metadata=dict(node.metadata),
    )

    # Store original node reference
    if original is not None:
        new_node.metadata["original_node"] = original
    else:
        new_node.metadata["original_node"] = node

    # Deep copy children
    for child in node.children:
        if isinstance(child, Node):
            child_copy = deep_copy_with_metadata(child, child if original is None else None)
            new_node.append(child_copy)
        elif isinstance(child, Text):
            new_node.append(Text(child.content))

    return new_node


def apply_filters_with_original(
    node: Node,
    filter_non_visible_tags: bool = True,
    filter_css_hidden: bool = True,
    filter_zero_dimensions: bool = True,
    filter_attributes_flag: bool = True,
    filter_empty_flag: bool = True,
    collapse_wrappers_flag: bool = True,
) -> Optional[Node]:
    """Apply filters while preserving original node references.

    Args:
        node: Original node tree
        filter_non_visible_tags: Remove script, style, head tags
        filter_css_hidden: Remove display:none, visibility:hidden elements
        filter_zero_dimensions: Remove zero-dimension elements
        filter_attributes_flag: Keep only semantic attributes
        filter_empty_flag: Remove empty nodes
        collapse_wrappers_flag: Collapse single-child wrappers

    Returns:
        Filtered node tree with original_node references in metadata
    """
    # First, deep copy to preserve original
    filtered = deep_copy_with_metadata(node)

    # Apply visibility filters
    if filter_non_visible_tags or filter_css_hidden or filter_zero_dimensions:
        filtered = filter_visible(filtered)
        if filtered is None:
            return None

    # Apply semantic filters
    if filter_attributes_flag:
        filtered = filter_attributes(filtered)
        if filtered is None:
            return None

    # Always filter presentational roles
    filtered = filter_presentational_roles(filtered)
    if filtered is None:
        return None

    if filter_empty_flag:
        filtered = filter_empty(filtered)
        if filtered is None:
            return None

    if collapse_wrappers_flag:
        filtered = collapse_single_child_wrappers(filtered)
        if filtered is None:
            return None

    return filtered


def generate_semantic_ids(node: Node) -> Tuple[Node, Dict[str, Node]]:
    """Generate semantic IDs for all element nodes.

    Generates readable IDs like "button-1", "input-2", "div-3" for LLM context.

    Args:
        node: Root node of tree

    Returns:
        Tuple of (node with IDs in metadata, dict mapping ID to node)
    """
    tag_counts: Dict[str, int] = {}
    id_mapping: Dict[str, Node] = {}

    def traverse(n: Node) -> None:
        """Recursively traverse and assign IDs."""
        # Count this tag
        tag = n.tag
        if tag not in tag_counts:
            tag_counts[tag] = 0
        tag_counts[tag] += 1

        # Generate ID
        semantic_id = f"{tag}-{tag_counts[tag]}"
        n.metadata["semantic_id"] = semantic_id
        id_mapping[semantic_id] = n

        # Traverse children
        for child in n.children:
            if isinstance(child, Node):
                traverse(child)

    traverse(node)
    return node, id_mapping
