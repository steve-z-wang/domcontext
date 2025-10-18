"""Text chunking utilities for splitting markdown into LLM-friendly chunks."""

from typing import List
from dataclasses import dataclass
from .ir.semantic_ir import SemanticIR
from ..tokenizer import Tokenizer


@dataclass
class Chunk:
    """A chunk of markdown text with token count."""
    markdown: str
    tokens: int


def chunk_semantic_ir(
    semantic_ir: SemanticIR,
    tokenizer: Tokenizer,
    size: int = 500,
    overlap: int = 50,
    include_parent_path: bool = True
) -> List[Chunk]:
    """Split semantic IR into chunks with overlap.

    Args:
        semantic_ir: SemanticIR to chunk
        tokenizer: Tokenizer for counting tokens
        size: Target chunk size in tokens
        overlap: Overlap between chunks in tokens
        include_parent_path: If True, add parent path and continuation indicators (default: True)

    Returns:
        List of Chunk objects with markdown and token count
    """
    if not include_parent_path:
        # Legacy behavior: simple line-based chunking
        markdown = semantic_ir.serialize_to_markdown()
        lines = markdown.split('\n')
        chunks = []
        current_chunk = []
        current_tokens = 0

        for line in lines:
            line_tokens = tokenizer.count_tokens(line + '\n')

            # If adding this line exceeds size, start new chunk
            if current_tokens + line_tokens > size and current_chunk:
                chunk_text = '\n'.join(current_chunk)
                chunks.append(Chunk(markdown=chunk_text, tokens=current_tokens))

                # Keep last few lines for overlap
                overlap_lines = []
                overlap_tokens = 0
                for prev_line in reversed(current_chunk):
                    prev_tokens = tokenizer.count_tokens(prev_line + '\n')
                    if overlap_tokens + prev_tokens <= overlap:
                        overlap_lines.insert(0, prev_line)
                        overlap_tokens += prev_tokens
                    else:
                        break

                current_chunk = overlap_lines
                current_tokens = overlap_tokens

            current_chunk.append(line)
            current_tokens += line_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append(Chunk(markdown=chunk_text, tokens=current_tokens))

        return chunks

    # New behavior: context-aware chunking with parent info and continuation
    from .ir.semantic_ir import SemanticElement

    # Collect all items from DFS traversal
    items = []
    for node, depth, path in semantic_ir.dfs(with_path=True):
        indent = "  " * depth
        markdown = f"{indent}- {node.data.to_markdown()}"
        items.append((node, depth, path, markdown))

    chunks = []
    start = 0

    while start < len(items):
        end = start
        tokens = 0

        # Walk until near limit
        while end < len(items):
            _, _, _, markdown = items[end]
            line_tokens = tokenizer.count_tokens(markdown)
            if tokens + line_tokens > size and end > start:
                break
            tokens += line_tokens
            end += 1

        # Create chunk
        chunk_items = items[start:end]

        # Build markdown with context
        lines = []

        # Add parent context with actual element info if not at start
        if start > 0 and chunk_items:
            _, first_depth, first_path, _ = chunk_items[0]
            # Show full parent hierarchy with actual IDs
            for i, ancestor_id in enumerate(first_path):
                indent = "  " * i
                lines.append(f"{indent}- {ancestor_id}")
            # Add ellipsis under last parent to indicate omitted content
            indent = "  " * first_depth
            lines.append(f"{indent}- ...")

        # Add actual content
        lines.extend([markdown for _, _, _, markdown in chunk_items])

        # Add continuation indicator if not at end
        if end < len(items):
            _, last_depth, _, _ = chunk_items[-1]
            indent = "  " * last_depth
            lines.append(f"{indent}- ...")

        markdown_text = "\n".join(lines)

        # Calculate actual tokens including parent path (for accurate reporting)
        # Note: 'tokens' variable only counts content, used for overlap calculation
        actual_tokens = tokenizer.count_tokens(markdown_text)

        chunks.append(Chunk(
            markdown=markdown_text,
            tokens=actual_tokens  # Store actual total tokens including parent path
        ))

        # Move pointer with overlap
        if end >= len(items):
            break

        overlap_count = 0
        overlap_tok = 0
        for i in range(end - 1, start - 1, -1):
            _, _, _, markdown = items[i]
            item_tokens = tokenizer.count_tokens(markdown)
            if overlap_tok + item_tokens > overlap:
                break
            overlap_tok += item_tokens
            overlap_count += 1

        start = end - max(overlap_count, 1)

    return chunks
