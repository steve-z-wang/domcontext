"""DomNode - Public API for DOM elements."""

from typing import Dict, List, Optional

from domnode import Node, Text


class DomNode:
    """Public API wrapper around domnode.Node.

    Provides clean interface for accessing element data and navigating DOM tree.
    """

    def __init__(self, node: Node):
        """Initialize DomNode from domnode.Node.

        Args:
            node: domnode.Node element
        """
        if not isinstance(node, Node):
            raise ValueError("DomNode requires a domnode.Node instance")

        self._node = node

    @property
    def tag(self) -> str:
        """HTML tag name (e.g., 'button', 'input', 'div')."""
        return self._node.tag

    @property
    def text(self) -> str:
        """All text content from this element and descendants (like innerText)."""
        return self._node.get_text()

    @property
    def attributes(self) -> Dict[str, str]:
        """All attributes from original HTML."""
        return self._node.attrib

    @property
    def semantic_id(self) -> Optional[str]:
        """Semantic ID like 'button-1', 'input-2' for LLM reference."""
        return self._node.metadata.get("semantic_id")

    @property
    def backend_node_id(self) -> Optional[int]:
        """Backend node ID from CDP (for evaluation/testing).

        Returns the backend_node_id from the original node if available.
        """
        # Check if this node has original_node reference
        original = self._node.metadata.get("original_node")
        if original is not None:
            return original.metadata.get("backend_node_id")
        return self._node.metadata.get("backend_node_id")

    @property
    def parent(self) -> Optional["DomNode"]:
        """Parent element in DOM tree."""
        if self._node.parent is None:
            return None
        return DomNode(self._node.parent)

    @property
    def children(self) -> List["DomNode"]:
        """Child elements (not text nodes) in DOM tree.

        Returns only element children, not text nodes.
        Text content is accessed via .text property.
        """
        result = []
        for child in self._node.children:
            if isinstance(child, Node):
                result.append(DomNode(child))
        return result

    def __repr__(self) -> str:
        if self.semantic_id:
            return f'DomNode(tag="{self.tag}", id="{self.semantic_id}")'
        return f'DomNode(tag="{self.tag}")'

    def __str__(self) -> str:
        attrs = ", ".join(f'{k}="{v}"' for k, v in list(self.attributes.items())[:3])
        if len(self.attributes) > 3:
            attrs += ", ..."
        return f"<{self.tag} {attrs}>" if attrs else f"<{self.tag}>"
