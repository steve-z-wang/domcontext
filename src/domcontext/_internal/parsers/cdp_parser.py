"""CDP (Chrome DevTools Protocol) snapshot parser.

Parses CDP DOMSnapshot.captureSnapshot responses into DomIR.
"""

from typing import Dict, List, Optional, Any
from ..ir.dom_ir import DomElement, DomText, DomTreeNode, BoundingBox, DomIR


def parse_cdp_snapshot(snapshot_data: Dict[str, Any]) -> DomIR:
    """
    Parse CDP DOMSnapshot response into DomIR.

    Args:
        snapshot_data: CDP DOMSnapshot.captureSnapshot response with:
            - documents: List of document snapshots
            - strings: Shared string table

    Returns:
        DomIR: Complete DOM tree with all CDP data
    """
    documents_data = snapshot_data.get('documents', [])
    strings = snapshot_data.get('strings', [])

    if not documents_data:
        # Empty document
        root_element = DomElement(tag="html", cdp_index=0)
        root_tree_node = DomTreeNode(data=root_element)
        return DomIR(root_tree_node)

    # Parse first document
    document_data = documents_data[0]
    nodes_data = document_data.get('nodes', {})
    layout_data = document_data.get('layout', {})

    # Helper to resolve string indices
    def get_string(index):
        if isinstance(index, int) and 0 <= index < len(strings):
            return strings[index]
        return ""

    # Extract parallel arrays
    node_types = nodes_data.get('nodeType', [])
    node_names = nodes_data.get('nodeName', [])
    node_values = nodes_data.get('nodeValue', [])
    parent_indices = nodes_data.get('parentIndex', [])
    attributes_arrays = nodes_data.get('attributes', [])

    # Layout data (optional)
    layout_node_indices = layout_data.get('nodeIndex', [])
    layout_bounds = layout_data.get('bounds', [])
    layout_styles = layout_data.get('styles', [])

    # Build layout lookup: node_index -> (bounds, styles)
    layout_map = {}
    for i, node_idx in enumerate(layout_node_indices):
        bounds = None
        if i < len(layout_bounds):
            b = layout_bounds[i]
            if len(b) >= 4:
                bounds = BoundingBox(x=b[0], y=b[1], width=b[2], height=b[3])

        styles = {}
        if i < len(layout_styles):
            style_pairs = layout_styles[i]
            for j in range(0, len(style_pairs), 2):
                if j + 1 < len(style_pairs):
                    name = get_string(style_pairs[j])
                    value = get_string(style_pairs[j + 1])
                    if name:
                        styles[name] = value

        layout_map[node_idx] = (bounds, styles)

    # Create DomElements and DomTreeNodes (first pass)
    tree_nodes: List[Optional[DomTreeNode]] = []
    num_nodes = len(node_types)

    for i in range(num_nodes):
        node_type = node_types[i] if i < len(node_types) else 0

        if node_type == 1:  # Element node
            # Parse attributes
            node_attrs = {}
            attributes = attributes_arrays[i] if i < len(attributes_arrays) else []
            for j in range(0, len(attributes), 2):
                if j + 1 < len(attributes):
                    attr_name = get_string(attributes[j])
                    attr_value = get_string(attributes[j + 1])
                    if attr_name and attr_value:
                        node_attrs[attr_name] = attr_value

            # Get tag name
            node_name_idx = node_names[i] if i < len(node_names) else None
            tag_name = get_string(node_name_idx).lower() if node_name_idx is not None else "unknown"

            # Get layout data
            bounds, styles = layout_map.get(i, (None, {}))

            # Create DomElement (data only)
            element = DomElement(
                tag=tag_name,
                cdp_index=i,
                attributes=node_attrs,
                styles=styles,
                bounds=bounds
            )

            # Create DomTreeNode wrapping the element
            tree_node = DomTreeNode(data=element)
            tree_nodes.append(tree_node)
        else:
            # Text node or other - placeholder
            tree_nodes.append(None)

    # Build tree relationships (second pass)
    root_tree_node = None

    for i in range(num_nodes):
        node_type = node_types[i] if i < len(node_types) else 0

        # Handle text nodes
        if node_type == 3:  # Text node
            parent_idx = parent_indices[i] if i < len(parent_indices) else None
            if parent_idx is not None and 0 <= parent_idx < len(tree_nodes):
                parent_tree_node = tree_nodes[parent_idx]
                if parent_tree_node:
                    node_value_idx = node_values[i] if i < len(node_values) else None
                    text_content = get_string(node_value_idx) if node_value_idx is not None else ""
                    if text_content.strip():
                        # Create DomText and wrap in DomTreeNode
                        text = DomText(text=text_content)
                        text_tree_node = DomTreeNode(data=text)
                        parent_tree_node.add_child(text_tree_node)  # Sets parent automatically
            continue

        # Handle element nodes
        current_tree_node = tree_nodes[i]
        if current_tree_node is None:
            continue

        # Link to parent
        parent_idx = parent_indices[i] if i < len(parent_indices) else None
        if parent_idx is not None and parent_idx != -1:
            if 0 <= parent_idx < len(tree_nodes):
                parent_tree_node = tree_nodes[parent_idx]
                if parent_tree_node:
                    parent_tree_node.add_child(current_tree_node)  # Sets parent automatically
        else:
            # Root node (parentIndex is -1 or None)
            if root_tree_node is None:
                root_tree_node = current_tree_node

    # Fallback to first element if no root found
    if root_tree_node is None:
        for tree_node in tree_nodes:
            if tree_node is not None:
                root_tree_node = tree_node
                break

    # Final fallback
    if root_tree_node is None:
        root_element = DomElement(tag="html", cdp_index=0)
        root_tree_node = DomTreeNode(data=root_element)

    return DomIR(root_tree_node)
