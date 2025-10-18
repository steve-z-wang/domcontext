"""HTML string parser for Mind2Web dataset.

Parses HTML strings (with embedded backend_node_id) into DomIR.
"""

from typing import Dict, Optional
from lxml import etree, html as lxml_html
from ..ir.dom_ir import DomElement, DomText, DomTreeNode, BoundingBox, DomIR


def parse_html(html_string: str) -> DomIR:
    """
    Parse HTML string into DomIR.

    Designed for Mind2Web dataset which has:
    - backend_node_id embedded as HTML attribute
    - bounding_box_rect as HTML attribute (optional)
    - Clean semantic HTML (already filtered)

    Args:
        html_string: HTML string with backend_node_id attributes

    Returns:
        DomIR: Complete DOM tree ready for filtering pipeline

    Example:
        >>> html = '<html backend_node_id="1"><body backend_node_id="2">...</body></html>'
        >>> dom_ir = parse_html(html)
    """
    # Handle empty HTML
    if not html_string or not html_string.strip():
        # Return empty DomIR with a minimal html element
        root_element = DomElement(tag="html")
        root_tree_node = DomTreeNode(data=root_element)
        return DomIR(root_tree_node)

    # Parse HTML with lxml
    try:
        # Try parsing as XML first (preserves custom tags like <text>)
        parser = etree.XMLParser(recover=True, remove_blank_text=False)
        tree = etree.fromstring(html_string.encode('utf-8'), parser=parser)
    except:
        # Fallback to HTML parser
        tree = lxml_html.fromstring(html_string)

    # Convert lxml tree to DomIR
    root_tree_node = _convert_lxml_to_dom_tree(tree)

    return DomIR(root_tree_node)


def _parse_bounding_box(bbox_str: str) -> Optional[BoundingBox]:
    """
    Parse bounding_box_rect attribute.

    Format: "x,y,width,height" (e.g., "339,117.5,27,17")

    Returns:
        BoundingBox or None if invalid
    """
    if not bbox_str:
        return None

    try:
        parts = bbox_str.split(',')
        if len(parts) >= 4:
            x, y, width, height = parts[:4]
            return BoundingBox(
                x=float(x),
                y=float(y),
                width=float(width),
                height=float(height)
            )
    except (ValueError, AttributeError):
        pass

    return None


def _convert_lxml_to_dom_tree(lxml_node, node_index: int = 0) -> DomTreeNode:
    """
    Recursively convert lxml Element to DomTreeNode.

    Args:
        lxml_node: lxml Element or text
        node_index: Auto-incrementing index for elements without backend_node_id

    Returns:
        DomTreeNode with DomElement or DomText
    """
    # Handle text nodes
    if isinstance(lxml_node, str):
        # Direct text content
        text_content = lxml_node.strip()
        if text_content:
            text_data = DomText(text=text_content)
            return DomTreeNode(data=text_data)
        return None

    # Get tag name
    tag_name = lxml_node.tag if isinstance(lxml_node.tag, str) else str(lxml_node.tag)
    tag_name = tag_name.lower()

    # Handle special Mind2Web <text> elements (they use custom tags)
    if tag_name == 'text':
        # This is a text content wrapper, extract the text
        text_content = (lxml_node.text or "").strip()
        if text_content:
            text_data = DomText(text=text_content)
            return DomTreeNode(data=text_data)
        return None

    # Extract attributes
    attributes = dict(lxml_node.attrib)

    # Parse backend_node_id if present
    backend_node_id = attributes.get('backend_node_id')
    cdp_index = int(backend_node_id) if backend_node_id else None

    # Parse bounding box if present
    bbox_str = attributes.get('bounding_box_rect', '')
    bounds = _parse_bounding_box(bbox_str)

    # Create DomElement
    element = DomElement(
        tag=tag_name,
        cdp_index=cdp_index,
        attributes=attributes,
        styles={},  # Mind2Web doesn't provide computed styles
        bounds=bounds
    )

    # Create TreeNode
    tree_node = DomTreeNode(data=element)

    # Process text content before first child
    if lxml_node.text:
        text_content = lxml_node.text.strip()
        if text_content:
            text_data = DomText(text=text_content)
            text_tree_node = DomTreeNode(data=text_data)
            tree_node.add_child(text_tree_node)

    # Process children
    for child in lxml_node:
        child_tree_node = _convert_lxml_to_dom_tree(child, node_index)
        if child_tree_node:
            tree_node.add_child(child_tree_node)

        # Process tail text (text after closing tag)
        if child.tail:
            tail_content = child.tail.strip()
            if tail_content:
                tail_data = DomText(text=tail_content)
                tail_tree_node = DomTreeNode(data=tail_data)
                tree_node.add_child(tail_tree_node)

    return tree_node
