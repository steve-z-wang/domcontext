"""SemanticIRSerializer - orchestrates serialization of entire IR."""

from typing import Iterator

from ..ir.semantic_ir import SemanticElement, SemanticIR, SemanticText
from .atomic_serializers import ElementNoAttrsSerializer, ElementSerializer, TextSerializer
from .types import Atom


class SemanticIRSerializer:
    """Orchestrates serialization of SemanticIR into atoms.

    Performs DFS traversal and delegates to node-specific serializers.
    Yields Atom objects - NO knowledge of tokens or chunking.
    """

    def __init__(self, semantic_ir: SemanticIR):
        """Initialize serializer.

        Args:
            semantic_ir: The semantic IR to serialize
        """
        self.semantic_ir = semantic_ir
        self.node_counter = 0

    def __iter__(self) -> Iterator[Atom]:
        """Yield atoms from DFS traversal of semantic IR."""
        for node, depth, path in self.semantic_ir.dfs(with_path=True):
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

    def _create_serializer(self, node, indent: str, node_id: int, path: list):
        """Factory: create appropriate serializer based on node type."""
        if isinstance(node.data, SemanticElement):
            element = node.data
            if element.semantic_attributes:
                return ElementSerializer(element, indent, node_id, path)
            else:
                return ElementNoAttrsSerializer(element, indent, node_id, path)
        elif isinstance(node.data, SemanticText):
            return TextSerializer(node.data, indent, node_id, path)
        else:
            raise ValueError(f"Unknown node type: {type(node.data)}")
