"""TreeSerializer - orchestrates serialization of entire Node tree."""

from typing import Iterator, List, Tuple

from domnode import Node, Text

from .atomic_serializers import ElementNoAttrsSerializer, ElementSerializer, TextSerializer
from .types import Atom


class TreeSerializer:
    """Orchestrates serialization of Node tree into atoms.

    Performs DFS traversal and delegates to node-specific serializers.
    Yields Atom objects - NO knowledge of tokens or chunking.
    """

    def __init__(self, root: Node):
        """Initialize serializer.

        Args:
            root: The root node to serialize
        """
        self.root = root
        self.node_counter = 0

    def __iter__(self) -> Iterator[Atom]:
        """Yield atoms from DFS traversal of node tree."""
        for node, depth, path in self._dfs_with_path(self.root):
            node_id = self.node_counter
            self.node_counter += 1

            # Build chunk_context (formatted parent path)
            chunk_context = ""
            if path:
                lines = []
                for depth_idx, ancestor_id in enumerate(path):
                    ancestor_indent = "  " * depth_idx
                    lines.append(f"{ancestor_indent}- {ancestor_id}\n")
                chunk_context = "".join(lines)

            # Create appropriate serializer based on node type
            indent = "  " * depth
            serializer = self._create_serializer(node, indent, node_id, path)

            # Yield atoms from this serializer
            for (
                content,
                line_start_first,
                line_start_cont,
                line_end_complete,
                line_end_cont,
                is_first,
                is_last,
            ) in serializer:

                yield Atom(
                    content=content,
                    chunk_context=chunk_context,
                    line_start_first=line_start_first,
                    line_start_cont=line_start_cont,
                    line_end_complete=line_end_complete,
                    line_end_cont=line_end_cont,
                    node_id=node_id,
                    is_first_in_node=is_first,
                    is_last_in_node=is_last,
                )

    def _dfs_with_path(self, root: Node) -> Iterator[Tuple[Node | Text, int, List[str]]]:
        """DFS traversal with depth and path tracking.

        Yields:
            (node, depth, path) where path is list of ancestor semantic IDs
        """

        def traverse(node: Node | Text, depth: int = 0, path: List[str] = None):
            if path is None:
                path = []

            # Yield this node
            yield (node, depth, path)

            # For Node, traverse children
            if isinstance(node, Node):
                # Build path for children
                semantic_id = node.metadata.get("semantic_id")
                node_id = semantic_id if semantic_id else node.tag
                new_path = path + [node_id]

                # Traverse children
                for child in node.children:
                    yield from traverse(child, depth + 1, new_path)

        yield from traverse(root, 0, [])

    def _create_serializer(self, node: Node | Text, indent: str, node_id: int, path: list):
        """Factory: create appropriate serializer based on node type."""
        if isinstance(node, Node):
            if node.attrib:
                return ElementSerializer(node, indent, node_id, path)
            else:
                return ElementNoAttrsSerializer(node, indent, node_id, path)
        elif isinstance(node, Text):
            return TextSerializer(node, indent, node_id, path)
        else:
            raise ValueError(f"Unknown node type: {type(node)}")
