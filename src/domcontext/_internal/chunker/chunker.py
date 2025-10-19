"""Main chunking algorithm - builds chunks from flat atom list."""

from typing import List, Optional, Tuple

from ...tokenizer import Tokenizer
from ..ir.semantic_ir import SemanticIR
from .chunk import Chunk
from .semantic_ir_serializer import SemanticIRSerializer
from .types import Atom


def chunk_semantic_ir(
    semantic_ir: SemanticIR,
    tokenizer: Tokenizer,
    size: int = 500,
    overlap: int = 50,
    include_parent_path: bool = True,
    max_unit_tokens: int = None,  # Kept for backward compat, not used
) -> List[Chunk]:
    """Split semantic IR into chunks with overlap.

    This function processes a flat list of atoms and builds chunks.
    All grouping and token logic happens here.

    Args:
        semantic_ir: SemanticIR to chunk
        tokenizer: Tokenizer for counting tokens
        size: Target chunk size in tokens
        overlap: Overlap between chunks in tokens
        include_parent_path: If True, add parent path (default: True)
        max_unit_tokens: Deprecated (kept for backward compatibility)

    Returns:
        List of Chunk objects
    """
    # Get flat list of atoms (serializer has NO tokenizer!)
    serializer = SemanticIRSerializer(semantic_ir)
    all_atoms = list(serializer)

    if not all_atoms:
        return []

    chunks = []
    i = 0  # Current atom index
    prev_chunk_last_node_id: Optional[int] = None  # For continuation detection

    while i < len(all_atoms):
        chunk = Chunk()
        chunk_start_idx = i
        atoms_in_chunk = []  # Track which atoms we added

        # Add chunk context (parent path) if not first chunk and enabled
        if chunks and include_parent_path and all_atoms[i].chunk_context:
            tokens = tokenizer.count_tokens(all_atoms[i].chunk_context)
            chunk.add_text(all_atoms[i].chunk_context, tokens)

        # Track current scope state
        current_scope_atoms = []  # Atoms accumulated in current scope
        current_scope_node_id = None

        # Add atoms until chunk is full
        while i < len(all_atoms):
            atom = all_atoms[i]

            # Check if starting a new scope
            if atom.is_first_in_node:
                # Flush previous scope if any
                if current_scope_atoms:
                    line, tokens = _build_and_count(current_scope_atoms, False, False, tokenizer)
                    if chunk.text_pieces and chunk.get_tokens() + tokens > size:
                        break
                    chunk.add_text(line, tokens)
                    atoms_in_chunk.extend(current_scope_atoms)
                    current_scope_atoms = []

                # Start new scope
                current_scope_node_id = atom.node_id
                current_scope_atoms = [atom]
                i += 1

                # CHECK: Would this atom fit? (worst case with continuation marker)
                test_line, test_tokens = _build_and_count(
                    current_scope_atoms, False, not atom.is_last_in_node, tokenizer
                )
                if chunk.text_pieces and chunk.get_tokens() + test_tokens > size:
                    # Won't fit - backtrack
                    i -= 1
                    current_scope_atoms = []
                    break

            else:
                # Continuing an existing node (not first atom)
                if not current_scope_atoms:
                    current_scope_node_id = atom.node_id

                # Try to add atom to current scope
                test_atoms = current_scope_atoms + [atom]
                is_cont = _is_continuation(
                    prev_chunk_last_node_id, current_scope_node_id, test_atoms
                )
                test_line, test_tokens = _build_and_count(
                    test_atoms, is_cont, not atom.is_last_in_node, tokenizer
                )

                # Check if fits
                if chunk.get_tokens() + test_tokens > size and current_scope_atoms:
                    # Doesn't fit - close current scope with continuation
                    line, tokens = _build_and_count(current_scope_atoms, is_cont, True, tokenizer)
                    chunk.add_text(line, tokens)
                    atoms_in_chunk.extend(current_scope_atoms)
                    current_scope_atoms = []
                    break

                # Fits - add it
                current_scope_atoms.append(atom)
                i += 1

            # Check if scope is complete
            if current_scope_atoms and current_scope_atoms[-1].is_last_in_node:
                is_cont = _is_continuation(
                    prev_chunk_last_node_id, current_scope_node_id, current_scope_atoms
                )
                line, tokens = _build_and_count(current_scope_atoms, is_cont, False, tokenizer)
                chunk.add_text(line, tokens)
                atoms_in_chunk.extend(current_scope_atoms)
                current_scope_atoms = []

        # Handle incomplete scope at end of chunk
        if current_scope_atoms:
            is_cont = _is_continuation(
                prev_chunk_last_node_id, current_scope_node_id, current_scope_atoms
            )
            line, tokens = _build_and_count(current_scope_atoms, is_cont, True, tokenizer)

            # Force add if chunk is empty, otherwise check if fits
            if not chunk.text_pieces:
                chunk.add_text(line, tokens)
                atoms_in_chunk.extend(current_scope_atoms)
            elif chunk.get_tokens() + tokens <= size:
                chunk.add_text(line, tokens)
                atoms_in_chunk.extend(current_scope_atoms)
            else:
                # Doesn't fit - backtrack
                i -= len(current_scope_atoms)

        # SAFETY: If no content atoms were added (only parent path), force add at least one
        if not atoms_in_chunk and i < len(all_atoms):
            atom = all_atoms[i]
            line, tokens = _build_and_count([atom], False, not atom.is_last_in_node, tokenizer)
            chunk.add_text(line, tokens)
            atoms_in_chunk.append(atom)
            i += 1

        # Track last node for continuation detection
        if atoms_in_chunk:
            prev_chunk_last_node_id = atoms_in_chunk[-1].node_id

        chunks.append(chunk)

        # Handle overlap - simple index backtracking!
        if i < len(all_atoms):
            overlap_start = _calculate_overlap_start(
                all_atoms, chunk_start_idx, i, overlap, tokenizer
            )
            if overlap_start > chunk_start_idx:
                i = overlap_start
                # Update continuation tracking
                if overlap_start > 0:
                    prev_chunk_last_node_id = all_atoms[overlap_start - 1].node_id
            # Otherwise continue from current position

    return chunks


def _is_continuation(
    prev_chunk_last_node_id: Optional[int], current_node_id: int, atoms: List[Atom]
) -> bool:
    """Check if we're continuing a node from the previous chunk."""
    return prev_chunk_last_node_id == current_node_id and atoms and not atoms[0].is_first_in_node


def _build_and_count(
    atoms: List[Atom], is_continuation: bool, has_more: bool, tokenizer: Tokenizer
) -> Tuple[str, int]:
    """Build a scope line and count its tokens.

    Returns:
        Tuple of (line, token_count)
    """
    line = _build_scope_line(atoms, is_continuation, has_more)
    tokens = tokenizer.count_tokens(line)
    return line, tokens


def _build_scope_line(atoms: List[Atom], is_continuation: bool, has_more: bool) -> str:
    """Build a line from a list of atoms in the same scope.

    Args:
        atoms: List of atoms in this scope
        is_continuation: True if continuing from previous chunk
        has_more: True if more atoms coming in scope

    Returns:
        Complete line string with newline
    """
    if not atoms:
        return ""

    # Element with no attributes/text (line_start has everything already)
    if atoms[0].content == "" and not atoms[0].line_end_complete:
        # Choose the right line_start
        if is_continuation:
            return f"{atoms[0].line_start_cont}\n"
        else:
            return f"{atoms[0].line_start_first}\n"

    # Choose opening (line_start already includes indent + id + marker)
    if is_continuation:
        line_start = atoms[0].line_start_cont
    else:
        line_start = atoms[0].line_start_first

    # Choose closing
    if has_more:
        line_end = atoms[-1].line_end_cont
    else:
        line_end = atoms[-1].line_end_complete

    # Join all atom contents
    content = " ".join(atom.content for atom in atoms if atom.content)

    return f"{line_start}{content}{line_end}\n"


def _calculate_overlap_start(
    all_atoms: List[Atom],
    chunk_start: int,
    chunk_end: int,
    overlap_tokens: int,
    tokenizer: Tokenizer,
) -> int:
    """Calculate where next chunk should start based on overlap.

    Simple index backtracking based on token budget.

    Args:
        all_atoms: List of all atoms
        chunk_start: Where current chunk started
        chunk_end: Where current chunk ended
        overlap_tokens: Target overlap size
        tokenizer: Tokenizer for counting

    Returns:
        Index where next chunk should start
    """
    if chunk_start >= chunk_end:
        return chunk_end

    # Count backwards to find overlap point
    accumulated = 0
    overlap_count = 0

    for i in range(chunk_end - 1, chunk_start - 1, -1):
        atom = all_atoms[i]
        # Estimate tokens for this atom (just content)
        atom_tokens = tokenizer.count_tokens(atom.content)

        if accumulated + atom_tokens > overlap_tokens:
            break

        accumulated += atom_tokens
        overlap_count += 1

    return max(chunk_end - overlap_count, chunk_start)
