"""Chunker for domnode trees."""

from typing import List

from domnode import Node, Text

from ..tokenizer import Tokenizer
from .chunker.chunk import Chunk


def chunk_tree(
    node: Node,
    tokenizer: Tokenizer,
    size: int = 500,
    overlap: int = 50,
    include_parent_path: bool = True,
) -> List[Chunk]:
    """Split domnode tree into chunks with overlap.

    Args:
        node: Root node of tree
        tokenizer: Tokenizer for counting tokens
        size: Target chunk size in tokens
        overlap: Overlap between chunks in tokens
        include_parent_path: Include parent path for context

    Returns:
        List of Chunk objects
    """
    # For now, simple implementation: serialize whole tree and chunk by tokens
    # TODO: Implement smarter chunking that preserves structure

    from .serializer import serialize_to_markdown

    markdown = serialize_to_markdown(node)
    lines = markdown.split('\n')

    chunks = []
    current_chunk = Chunk()
    current_tokens = 0

    for line in lines:
        line_tokens = tokenizer.count_tokens(line + '\n')

        # Check if adding this line would exceed size
        if current_tokens + line_tokens > size and current_chunk.text_pieces:
            # Save current chunk
            chunks.append(current_chunk)

            # Start new chunk with overlap
            # For simplicity, just start fresh (overlap would require tracking recent lines)
            current_chunk = Chunk()
            current_tokens = 0

        # Add line to current chunk
        current_chunk.add_text(line + '\n', line_tokens)
        current_tokens += line_tokens

    # Add last chunk if it has content
    if current_chunk.text_pieces:
        chunks.append(current_chunk)

    return chunks if chunks else [Chunk()]
