"""Semantic IR - Filtered semantic tree for LLM resolution.

Contains:
- SemanticElement: Element data with ONLY semantic attributes
- SemanticText: Text content
- SemanticTreeNode: Tree node WITHOUT parent (lightweight)
- SemanticIR: Semantic tree for resolution
"""

from typing import Optional, List, Dict, Union


class SemanticElement:
    """Element data with ONLY semantic attributes.

    Pure data container - no tree structure.
    Created during semantic filtering.
    References back to DomTreeNode for navigation.
    """

    def __init__(
        self,
        tag: str,
        semantic_attributes: Optional[Dict[str, str]] = None,
        dom_tree_node: Optional['DomTreeNode'] = None,  # type: ignore
        readable_id: Optional[str] = None
    ):
        self.tag = tag
        self.semantic_attributes = semantic_attributes or {}
        self.dom_tree_node = dom_tree_node  # Reference to DomIR for navigation
        self.readable_id = readable_id  # LLM-friendly ID like "button-1", "input-2"

    def to_markdown(self) -> str:
        """
        Serialize element to markdown format.

        Returns:
            Markdown string like "button-1 (type="submit" name="btnK")"
        """
        parts = []

        # Add readable ID if available
        if self.readable_id:
            parts.append(self.readable_id)
        else:
            parts.append(self.tag)

        # Add attributes
        if self.semantic_attributes:
            attr_strs = [f'{k}="{v}"' for k, v in self.semantic_attributes.items()]
            parts.append(f'({" ".join(attr_strs)})')

        return " ".join(parts)

    def __repr__(self) -> str:
        id_str = f", id={self.readable_id}" if self.readable_id else ""
        return f'SemanticElement(tag="{self.tag}", attrs={len(self.semantic_attributes)}{id_str})'


class SemanticText:
    """Text content data.

    Pure data container - no tree structure.
    References back to DomTreeNode.
    """

    def __init__(
        self,
        text: str,
        dom_tree_node: Optional['DomTreeNode'] = None  # type: ignore
    ):
        self.text = text
        self.dom_tree_node = dom_tree_node

    def to_markdown(self) -> str:
        """
        Serialize text to markdown format.

        Returns:
            Quoted text string like '"Search"'
        """
        return f'"{self.text}"'

    def __repr__(self) -> str:
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f'SemanticText(text="{preview}")'


class SemanticTreeNode:
    """Tree node WITHOUT parent for semantic tree.

    Lightweight tree structure for resolution.
    No parent reference - only children.

    Contains:
    - data: SemanticElement or SemanticText
    - children: Child TreeNodes
    """

    def __init__(self, data: Union[SemanticElement, SemanticText]):
        self.data = data
        self.children: List['SemanticTreeNode'] = []

    def add_child(self, child: 'SemanticTreeNode') -> None:
        """Add a child node."""
        self.children.append(child)

    def get_element_children(self) -> List['SemanticTreeNode']:
        """Get only element children (not text)."""
        return [c for c in self.children if isinstance(c.data, SemanticElement)]

    def get_text_children(self) -> List['SemanticTreeNode']:
        """Get only text children."""
        return [c for c in self.children if isinstance(c.data, SemanticText)]

    def get_all_text(self) -> str:
        """Get all text content recursively."""
        text_parts = []
        for child in self.children:
            if isinstance(child.data, SemanticText):
                text_parts.append(child.data.text)
            elif isinstance(child.data, SemanticElement):
                text_parts.append(child.get_all_text())
        return " ".join(text_parts).strip()

    def __repr__(self) -> str:
        data_type = type(self.data).__name__
        return f'SemanticTreeNode(data={data_type}, children={len(self.children)})'


class SemanticIR:
    """Filtered semantic tree for LLM resolution.

    Tree of SemanticTreeNode objects.
    Created by semantic filtering pass.
    Lightweight - no parent references.
    """

    def __init__(self, root: SemanticTreeNode, id_index: Optional[Dict[str, SemanticElement]] = None):
        """
        Initialize SemanticIR.

        Args:
            root: Root SemanticTreeNode
            id_index: Pre-built mapping from readable_id → SemanticElement (optional)
        """
        self.root = root
        self._element_index: Optional[Dict[SemanticElement, SemanticTreeNode]] = None
        self._id_index = id_index  # Pre-built by generate_ids_pass

    def _build_index(self) -> None:
        """Build index of all SemanticElement → SemanticTreeNode."""
        self._element_index = {}

        def index_recursive(node: SemanticTreeNode):
            if isinstance(node.data, SemanticElement):
                self._element_index[node.data] = node
            for child in node.children:
                index_recursive(child)

        index_recursive(self.root)

    def get_node_by_element(self, element: SemanticElement) -> Optional[SemanticTreeNode]:
        """Get TreeNode containing this SemanticElement."""
        if self._element_index is None:
            self._build_index()
        return self._element_index.get(element)

    def get_element_by_id(self, readable_id: str) -> Optional[SemanticElement]:
        """
        Get SemanticElement by its readable ID.

        Args:
            readable_id: Readable ID like "button-1", "input-2"

        Returns:
            SemanticElement with that ID, or None if not found

        Note:
            ID index is pre-built during semantic_pass for efficiency.
        """
        if self._id_index is None:
            return None  # Index not built yet (shouldn't happen normally)
        return self._id_index.get(readable_id)

    def get_all_elements_with_ids(self) -> Dict[str, SemanticElement]:
        """
        Get all elements mapped by their readable IDs.

        Returns:
            Dictionary mapping readable_id → SemanticElement

        Note:
            ID index is pre-built during semantic_pass for efficiency.
        """
        if self._id_index is None:
            return {}  # Index not built yet (shouldn't happen normally)
        return dict(self._id_index)  # Return copy

    def all_element_nodes(self) -> List[SemanticTreeNode]:
        """Get all TreeNodes containing SemanticElement (not text)."""
        if self._element_index is None:
            self._build_index()
        return list(self._element_index.values())

    def dfs(self, with_depth: bool = False, with_path: bool = False):
        """
        Depth-first traversal generator.

        Args:
            with_depth: If True, includes depth in output
            with_path: If True, includes ancestor path in output

        Yields:
            - node only (default)
            - (node, depth) if with_depth=True
            - (node, depth, path) if with_path=True (implies with_depth)

        Example:
            >>> for node in semantic_ir.dfs():
            ...     print(node.data.to_markdown())
            >>>
            >>> for node, depth in semantic_ir.dfs(with_depth=True):
            ...     print("  " * depth + node.data.to_markdown())
            >>>
            >>> for node, depth, path in semantic_ir.dfs(with_path=True):
            ...     print(f"Path: {path}, Depth: {depth}")
        """
        def traverse(node: SemanticTreeNode, depth: int = 0, path: List[str] = None):
            if path is None:
                path = []

            # Yield based on flags
            if with_path:
                yield (node, depth, path.copy())
            elif with_depth:
                yield (node, depth)
            else:
                yield node

            # Build path for next level
            node_id = None
            if isinstance(node.data, SemanticElement) and node.data.readable_id:
                node_id = node.data.readable_id
            elif isinstance(node.data, SemanticElement):
                node_id = node.data.tag

            new_path = path + [node_id] if node_id else path

            # Traverse children
            for child in node.children:
                yield from traverse(child, depth + 1, new_path)

        yield from traverse(self.root, 0, [])

    def serialize_to_markdown(self) -> str:
        """
        Serialize to markdown bullet list format.

        Returns:
            Markdown string with indented bullet list

        Example:
            - body-1
              - div-1 (role="navigation")
                - a-1
                  - "About"
        """
        lines = []

        for node, depth in self.dfs(with_depth=True):
            indent = "  " * depth
            markdown = node.data.to_markdown()
            lines.append(f"{indent}- {markdown}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """
        Serialize SemanticIR to dictionary.

        Returns:
            Dictionary with root and total_nodes
        """
        def node_to_dict(node: SemanticTreeNode) -> dict:
            if isinstance(node.data, SemanticElement):
                elem = node.data
                result = {
                    'type': 'element',
                    'tag': elem.tag,
                    'readable_id': elem.readable_id,
                    'attributes': elem.semantic_attributes,
                    'children': [node_to_dict(child) for child in node.children]
                }
            else:  # SemanticText
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
        root_tag = self.root.data.tag if isinstance(self.root.data, SemanticElement) else "unknown"
        return f'SemanticIR(root="{root_tag}", total_nodes={total})'
