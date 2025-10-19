"""Text chunking utilities for splitting markdown into LLM-friendly chunks."""

from typing import List, Tuple
from dataclasses import dataclass, field
from .ir.semantic_ir import SemanticIR
from ..tokenizer import Tokenizer


@dataclass
class Chunk:
    """Generic chunk container - stores lines with token tracking.

    This is a reusable component for any chunking algorithm.
    It simply accumulates lines, tracks token count, and outputs markdown.
    """
    lines: List[Tuple[str, int]] = field(default_factory=list)  # (line, tokens)
    _total_tokens: int = field(default=0, init=False, repr=False)  # Running sum

    def add_line(self, line: str, tokens: int):
        """Add a line with its pre-calculated token count."""
        self.lines.append((line, tokens))
        self._total_tokens += tokens

    def get_tokens(self) -> int:
        """Get total tokens (O(1))."""
        return self._total_tokens

    def to_markdown(self) -> str:
        """Convert to markdown string."""
        return "\n".join(line for line, _ in self.lines)

    @property
    def markdown(self) -> str:
        """Backward compatibility: get markdown as property."""
        return self.to_markdown()

    @property
    def tokens(self) -> int:
        """Backward compatibility: get tokens as property."""
        return self.get_tokens()


def _collect_lines(
    semantic_ir: SemanticIR,
    tokenizer: Tokenizer,
    max_line_tokens: int = 500
) -> List[Tuple[str, int, List[str]]]:
    """Collect all lines from DFS traversal with their metadata.

    Args:
        semantic_ir: SemanticIR to collect lines from
        tokenizer: Tokenizer for counting tokens
        max_line_tokens: Maximum tokens per line; longer lines are truncated

    Returns:
        List of (markdown_line, tokens, parent_path) tuples
    """
    lines = []
    for node, depth, path in semantic_ir.dfs(with_path=True):
        indent = "  " * depth
        markdown = f"{indent}- {node.data.to_markdown()}"
        tokens = tokenizer.count_tokens(markdown)

        # Truncate if line exceeds token limit
        if tokens > max_line_tokens:
            # Binary search to find truncation point
            left, right = 0, len(markdown)
            while left < right:
                mid = (left + right + 1) // 2
                truncated = markdown[:mid] + "..."
                if tokenizer.count_tokens(truncated) <= max_line_tokens:
                    left = mid
                else:
                    right = mid - 1

            markdown = markdown[:left] + "..."
            tokens = tokenizer.count_tokens(markdown)

        lines.append((markdown, tokens, path))
    return lines


def _calculate_overlap_start(
    all_lines: List[Tuple[str, int, List[str]]],
    chunk_start: int,
    chunk_end: int,
    overlap_tokens: int
) -> int:
    """Calculate where the next chunk should start based on overlap.

    Args:
        all_lines: The full list of lines with metadata
        chunk_start: Index in all_lines where current chunk started
        chunk_end: Index in all_lines where current chunk ended (exclusive)
        overlap_tokens: Target overlap size in tokens

    Returns:
        Index where next chunk should start
    """
    if chunk_start >= chunk_end:
        return chunk_end

    # Count backwards from chunk_end to find overlap point
    accumulated = 0
    overlap_count = 0

    for i in range(chunk_end - 1, chunk_start - 1, -1):
        _, tokens, _ = all_lines[i]
        if accumulated + tokens > overlap_tokens:
            break
        accumulated += tokens
        overlap_count += 1

    # Backtrack by overlap_count items
    # Note: Returning chunk_start is OK - main loop always makes progress
    # by adding at least one line before checking size
    return max(chunk_end - overlap_count, chunk_start)


def chunk_semantic_ir(
    semantic_ir: SemanticIR,
    tokenizer: Tokenizer,
    size: int = 500,
    overlap: int = 50,
    include_parent_path: bool = True,
    max_line_tokens: int = None
) -> List[Chunk]:
    """Split semantic IR into chunks with overlap.

    Args:
        semantic_ir: SemanticIR to chunk
        tokenizer: Tokenizer for counting tokens
        size: Target chunk size in tokens
        overlap: Overlap between chunks in tokens
        include_parent_path: If True, add parent path (default: True)
        max_line_tokens: Maximum tokens per line; defaults to size if not set

    Returns:
        List of Chunk objects with markdown lines and token counts
    """
    # Default max_line_tokens to chunk size if not specified
    if max_line_tokens is None:
        max_line_tokens = size

    # Collect all lines with metadata
    all_lines = _collect_lines(semantic_ir, tokenizer, max_line_tokens)

    chunks = []
    i = 0

    while i < len(all_lines):
        chunk = Chunk()
        chunk_start = i  # Track where this chunk starts in all_lines
        content_lines_added = 0  # Track how many content lines we actually added

        # Add parent path lines if not first chunk and include_parent_path is enabled
        if i > 0 and include_parent_path:
            _, _, parent_path = all_lines[i]
            if parent_path:
                for depth, ancestor_id in enumerate(parent_path):
                    indent = "  " * depth
                    line = f"{indent}- {ancestor_id}"
                    tokens = tokenizer.count_tokens(line)
                    chunk.add_line(line, tokens)

        # Add content lines until chunk is full
        while i < len(all_lines):
            line, tokens, _ = all_lines[i]
            # Check if adding this line would exceed size limit
            if chunk.lines and chunk.get_tokens() + tokens > size:
                break
            chunk.add_line(line, tokens)
            content_lines_added += 1
            i += 1

        # Safety check: if we didn't add any content lines, force add one to make progress
        forced_add = False
        if content_lines_added == 0 and i < len(all_lines):
            line, tokens, _ = all_lines[i]
            chunk.add_line(line, tokens)
            i += 1
            forced_add = True

        chunks.append(chunk)

        # Handle overlap - backtrack i to include some items in next chunk
        # But skip overlap if we had to force-add (chunk is already struggling to fit content)
        if i < len(all_lines) and not forced_add:
            chunk_end = i  # Where this chunk ended in all_lines
            next_i = _calculate_overlap_start(all_lines, chunk_start, chunk_end, overlap)

            # Only use overlap if it actually moves us forward from chunk_start
            if next_i > chunk_start:
                i = next_i
            else:
                # Overlap would take us back to where we started or earlier, skip it
                i = chunk_end

    return chunks
