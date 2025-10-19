"""Type definitions for chunker."""

from dataclasses import dataclass


@dataclass
class Atom:
    """Raw atom representing individual attribute or word.

    Each atom carries pre-formatted text for different contexts.
    The chunker decides which text to use based on chunk/line state.
    """

    content: str  # Just the atom: 'type="submit"' or 'hello'

    # Chunk level - parent path to show when starting new chunk
    chunk_context: str  # "- body-1\n  - div-1\n" (already formatted)

    # Line level - how to start the line for this node
    line_start_first: str  # "  - btn-1 (" (first time, includes indent + id + marker)
    line_start_cont: str  # "  - btn-1 (... " (continuing from prev chunk)

    # Line endings
    line_end_complete: str  # ")" (node complete)
    line_end_cont: str  # " ...)" (more atoms coming)

    # Metadata for chunker logic
    node_id: int  # Unique node identifier (for continuation detection)
    is_first_in_node: bool  # First atom of this logical node
    is_last_in_node: bool  # Last atom of this logical node
