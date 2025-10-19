"""Serialization for domnode trees to markdown format."""

from domnode import Node, Text


def serialize_to_markdown(node: Node) -> str:
    """Serialize domnode tree to markdown bullet list format.

    Args:
        node: Root node of tree

    Returns:
        Markdown string with indented bullet list

    Example:
        - body-1
          - div-1 (role="navigation")
            - a-1
              - "About"
    """
    lines = []

    def traverse(n: Node, depth: int = 0):
        """Recursively traverse and build markdown."""
        indent = "  " * depth

        # Get semantic ID or fallback to tag
        semantic_id = n.metadata.get("semantic_id", n.tag)

        # Format attributes
        attr_parts = []
        if n.attrib:
            attr_strs = [f'{k}="{v}"' for k, v in n.attrib.items()]
            attr_parts.append(f'({" ".join(attr_strs)})')

        # Build line
        markdown = f"{semantic_id}"
        if attr_parts:
            markdown += f" {' '.join(attr_parts)}"

        lines.append(f"{indent}- {markdown}")

        # Process children
        for child in n.children:
            if isinstance(child, Node):
                traverse(child, depth + 1)
            elif isinstance(child, Text):
                # Add text nodes as quoted strings
                text_indent = "  " * (depth + 1)
                lines.append(f'{text_indent}- "{child.content}"')

    traverse(node, 0)
    return "\n".join(lines)
