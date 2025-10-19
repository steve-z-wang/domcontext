"""Atomic serializers for individual nodes (elements, text)."""

from abc import ABC, abstractmethod
from typing import Iterator

from domnode import Node, Text


class AtomicSerializer(ABC):
    """Base class for serializing a single node into atoms.

    Each serializer handles one node and yields individual atoms (attributes/words).
    NO tokenizer - just pure serialization.
    """

    def __init__(self, indent: str, node_id: int, path: list):
        """Initialize serializer with common metadata.

        Args:
            indent: Indentation string (e.g., "  ")
            node_id: Unique node identifier
            path: Parent path for context
        """
        self.indent = indent
        self.node_id = node_id
        self.path = path

    @abstractmethod
    def __iter__(self) -> Iterator[tuple]:
        """Yield atoms for this node.

        Yields:
            Tuple of (content, line_start_first, line_start_cont,
                     line_end_complete, line_end_cont, is_first, is_last)

            Where line_start_first/cont are pre-formatted strings like:
            - "  - btn-1 (" (includes indent, id, marker)
            - '  - "' (for text nodes)
        """
        pass


class ElementNoAttrsSerializer(AtomicSerializer):
    """Serializes element without attributes - single atom with no scope."""

    def __init__(self, node: Node, indent: str, node_id: int, path: list):
        super().__init__(indent, node_id, path)
        self.node = node
        semantic_id = node.metadata.get("semantic_id")
        self.base_id = semantic_id if semantic_id else node.tag

    def __iter__(self):
        """Yield single atom for element without attributes."""
        # Build formatted line starts (no scope markers for elements without attrs)
        line_start = f"{self.indent}- {self.base_id}"

        yield (
            "",  # content (empty - just element ID in line_start)
            line_start,  # line_start_first
            line_start,  # line_start_cont (same, no continuation markers)
            "",  # line_end_complete
            "",  # line_end_cont
            True,  # is_first
            True,  # is_last
        )


class ElementSerializer(AtomicSerializer):
    """Serializes element attributes - yields individual attributes."""

    def __init__(self, node: Node, indent: str, node_id: int, path: list):
        super().__init__(indent, node_id, path)
        self.node = node
        semantic_id = node.metadata.get("semantic_id")
        self.base_id = semantic_id if semantic_id else node.tag

    def __iter__(self):
        """Yield individual attribute atoms."""
        attrs = list(self.node.attrib.items())

        for i, (key, value) in enumerate(attrs):
            is_first = i == 0
            is_last = i == len(attrs) - 1

            content = f'{key}="{value}"'

            # Build formatted line starts with indent, id, and opening marker
            line_start_first = f"{self.indent}- {self.base_id} ("
            line_start_cont = f"{self.indent}- {self.base_id} (... "

            # Line endings
            line_end_complete = ")"
            line_end_cont = " ...)"

            yield (
                content,
                line_start_first,
                line_start_cont,
                line_end_complete,
                line_end_cont,
                is_first,
                is_last,
            )


class TextSerializer(AtomicSerializer):
    """Serializes text - yields individual words."""

    def __init__(self, text: Text, indent: str, node_id: int, path: list):
        super().__init__(indent, node_id, path)
        self.text = text

    def __iter__(self):
        """Yield individual word atoms."""
        words = self.text.content.split()

        if not words:
            # Empty text - yield empty atom
            line_start_first = f'{self.indent}- "'
            line_start_cont = f'{self.indent}- "... '

            yield (
                "",  # content
                line_start_first,  # line_start_first
                line_start_cont,  # line_start_cont
                '"',  # line_end_complete
                ' ..."',  # line_end_cont
                True,  # is_first
                True,  # is_last
            )
            return

        for i, word in enumerate(words):
            is_first = i == 0
            is_last = i == len(words) - 1

            # Build formatted line starts with indent and quote marker
            line_start_first = f'{self.indent}- "'
            line_start_cont = f'{self.indent}- "... '

            # Line endings with quotes
            line_end_complete = '"'
            line_end_cont = ' ..."'

            yield (
                word,
                line_start_first,
                line_start_cont,
                line_end_complete,
                line_end_cont,
                is_first,
                is_last,
            )
