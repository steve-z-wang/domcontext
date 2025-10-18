"""DomNode - Public API for DOM elements."""

from typing import List, Optional, Dict
from ._internal.ir.dom_ir import DomElement, DomTreeNode


class DomNode:
    """Public API wrapper around DOM tree node.

    Provides clean interface for accessing element data and navigating DOM tree.
    """

    def __init__(self, dom_tree_node: DomTreeNode):
        """Initialize DomNode from DOM tree node.

        Args:
            dom_tree_node: DomTreeNode containing element data
        """
        if not isinstance(dom_tree_node.data, DomElement):
            raise ValueError("DomNode can only wrap element nodes, not text nodes")

        self._node = dom_tree_node

    @property
    def tag(self) -> str:
        """HTML tag name (e.g., 'button', 'input', 'div')."""
        return self._node.data.tag

    @property
    def text(self) -> str:
        """All text content from this element and descendants (like innerText)."""
        return self._node.get_all_text()

    @property
    def attributes(self) -> Dict[str, str]:
        """All attributes from original HTML."""
        return self._node.data.attributes

    @property
    def backend_node_id(self) -> Optional[int]:
        """Backend node ID from CDP (for evaluation/testing)."""
        return self._node.data.cdp_index

    @property
    def parent(self) -> Optional['DomNode']:
        """Parent element in DOM tree."""
        if self._node.parent is None:
            return None

        # Walk up until we find an element (skip text nodes)
        current = self._node.parent
        while current is not None:
            if isinstance(current.data, DomElement):
                return DomNode(current)
            current = current.parent

        return None

    @property
    def children(self) -> List['DomNode']:
        """Child elements (not text nodes) in DOM tree.

        Returns only element children, not text nodes.
        Text content is accessed via .text property.
        """
        return [DomNode(child) for child in self._node.get_element_children()]

    def __repr__(self) -> str:
        return f'DomNode(tag="{self.tag}")'

    def __str__(self) -> str:
        attrs = ", ".join(f'{k}="{v}"' for k, v in list(self.attributes.items())[:3])
        if len(self.attributes) > 3:
            attrs += ", ..."
        return f'<{self.tag} {attrs}>'
