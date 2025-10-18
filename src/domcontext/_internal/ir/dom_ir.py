"""DOM IR - Complete DOM tree with all CDP data.

Contains:
- DomElement: Element data with ALL CDP details
- DomText: Text content
- DomTreeNode: Tree node WITH parent for navigation
- DomIR: Complete DOM tree
"""

from typing import Optional, List, Dict, Union
from dataclasses import dataclass


@dataclass
class BoundingBox:
    """Bounding box coordinates from CDP layout data."""
    x: float
    y: float
    width: float
    height: float


class DomElement:
    """Element data with ALL CDP details.

    Pure data container - no tree structure.
    Created during CDP parsing.
    """

    def __init__(
        self,
        tag: str,
        cdp_index: Optional[int] = None,
        attributes: Optional[Dict[str, str]] = None,
        styles: Optional[Dict[str, str]] = None,
        bounds: Optional[BoundingBox] = None
    ):
        self.tag = tag
        self.cdp_index = cdp_index
        self.attributes = attributes or {}
        self.styles = styles or {}
        self.bounds = bounds

    def __repr__(self) -> str:
        return f'DomElement(tag="{self.tag}", attrs={len(self.attributes)})'


class DomText:
    """Text content data.

    Pure data container - no tree structure.
    """

    def __init__(self, text: str):
        self.text = text

    def __repr__(self) -> str:
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f'DomText(text="{preview}")'


class DomTreeNode:
    """Tree node WITH parent for DOM navigation.

    Contains:
    - data: DomElement or DomText
    - parent: Parent TreeNode (None for root)
    - children: Child TreeNodes
    """

    def __init__(self, data: Union[DomElement, DomText]):
        self.data = data
        self.parent: Optional['DomTreeNode'] = None
        self.children: List['DomTreeNode'] = []

    def add_child(self, child: 'DomTreeNode') -> None:
        """Add a child node and set its parent."""
        self.children.append(child)
        child.parent = self

    def get_element_children(self) -> List['DomTreeNode']:
        """Get only element children (not text)."""
        return [c for c in self.children if isinstance(c.data, DomElement)]

    def get_text_children(self) -> List['DomTreeNode']:
        """Get only text children."""
        return [c for c in self.children if isinstance(c.data, DomText)]

    def get_all_text(self) -> str:
        """Get all text content recursively."""
        text_parts = []
        for child in self.children:
            if isinstance(child.data, DomText):
                text_parts.append(child.data.text)
            elif isinstance(child.data, DomElement):
                text_parts.append(child.get_all_text())
        return " ".join(text_parts).strip()

    def walk_up(self) -> List['DomTreeNode']:
        """Walk up to root, returning path (bottom to top)."""
        path = []
        current = self
        while current is not None:
            path.append(current)
            current = current.parent
        return path

    def __repr__(self) -> str:
        data_type = type(self.data).__name__
        return f'DomTreeNode(data={data_type}, children={len(self.children)})'


class DomIR:
    """Complete DOM tree with all CDP data.

    Tree of DomTreeNode objects.
    Created by CDP parser.
    """

    def __init__(self, root: DomTreeNode):
        self.root = root
        self._element_index: Optional[Dict[DomElement, DomTreeNode]] = None

    def _build_index(self) -> None:
        """Build index of all DomElement → DomTreeNode."""
        self._element_index = {}

        def index_recursive(node: DomTreeNode):
            if isinstance(node.data, DomElement):
                self._element_index[node.data] = node
            for child in node.children:
                index_recursive(child)

        index_recursive(self.root)

    def get_node_by_element(self, element: DomElement) -> Optional[DomTreeNode]:
        """Get TreeNode containing this DomElement."""
        if self._element_index is None:
            self._build_index()
        return self._element_index.get(element)

    def all_element_nodes(self) -> List[DomTreeNode]:
        """Get all TreeNodes containing DomElement (not text)."""
        if self._element_index is None:
            self._build_index()
        return list(self._element_index.values())

    def to_dict(self) -> dict:
        """
        Serialize DomIR to dictionary.

        Returns:
            Dictionary with root and total_nodes
        """
        def node_to_dict(node: DomTreeNode) -> dict:
            if isinstance(node.data, DomElement):
                elem = node.data
                result = {
                    'type': 'element',
                    'tag': elem.tag,
                    'attributes': elem.attributes,
                    'styles': elem.styles,
                    'bounds': {
                        'x': elem.bounds.x,
                        'y': elem.bounds.y,
                        'width': elem.bounds.width,
                        'height': elem.bounds.height
                    } if elem.bounds else None,
                    'children': [node_to_dict(child) for child in node.children]
                }
            else:  # DomText
                result = {
                    'type': 'text',
                    'text': node.data.text
                }
            return result

        return {
            'root': node_to_dict(self.root),
            'total_nodes': len(self.all_element_nodes())
        }

    def __repr__(self) -> str:
        total = len(self.all_element_nodes())
        root_tag = self.root.data.tag if isinstance(self.root.data, DomElement) else "unknown"
        return f'DomIR(root="{root_tag}", total_nodes={total})'
