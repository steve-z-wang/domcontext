"""Semantic filtering: DomIR → SemanticIR.

Converts DomIR to SemanticIR by:
1. Converting DomTreeNode → SemanticTreeNode (with dom_tree_node references)
2. Filtering out non-semantic elements
3. Extracting only semantic attributes
4. Creating clean SemanticIR tree
5. Generating readable IDs for LLM (button-1, input-2, etc.)

Note: Non-visible tags (script, style, head, etc.) are already filtered in visibility_pass!

Five-pass pipeline:
0. convert_to_semantic: DomTreeNode → SemanticTreeNode (pure conversion)
1. filter_by_attributes: Remove aria-hidden/role="presentation", keep only semantic attributes
2. filter_empty_nodes: Remove nodes with no attributes and no children
3. collapse_wrappers: Collapse single-child wrappers with no attributes
4. generate_ids: Assign readable IDs like "button-1", "input-2" for LLM
"""

from typing import Optional
from ..ir.dom_ir import DomIR
from ..ir.semantic_ir import SemanticIR
from .semantic.convert import convert_to_semantic_pass
from .semantic.filter_attributes import filter_by_attributes_pass
from .semantic.filter_empty import filter_empty_nodes_pass
from .semantic.collapse_wrappers import collapse_wrappers_pass


def semantic_pass(
    dom_ir: DomIR,
    filter_attributes: bool = True,
    filter_empty: bool = True,
    collapse_wrappers: bool = True
) -> Optional[SemanticIR]:
    """
    Create SemanticIR from DomIR through five passes.

    Args:
        dom_ir: DomIR with visible elements (script/style/head already filtered)
        filter_attributes: Keep only semantic attributes
        filter_empty: Remove empty nodes
        collapse_wrappers: Collapse single-child wrappers

    Returns:
        SemanticIR: Semantic IR with SemanticElement/SemanticTreeNode and readable IDs, or None if empty
    """
    # Pass 0: Convert DomTreeNode → SemanticTreeNode (always needed)
    root = convert_to_semantic_pass(dom_ir.root)

    # Pass 1: Filter by attributes (aria-hidden, role="presentation", etc.)
    if filter_attributes:
        root = filter_by_attributes_pass(root)
        if root is None:
            return None

    # Pass 2: Filter empty nodes
    if filter_empty:
        root = filter_empty_nodes_pass(root)
        if root is None:
            return None

    # Pass 3: Collapse wrappers
    if collapse_wrappers:
        root = collapse_wrappers_pass(root)
        if root is None:
            return None

    # Pass 4: Generate readable IDs for LLM and build ID mapping in single traversal (always needed)
    from .semantic.generate_ids import generate_ids_pass
    root, id_mapping = generate_ids_pass(root)

    # Create SemanticIR with pre-built ID index (fully formed!)
    semantic_ir = SemanticIR(root, id_index=id_mapping)

    return semantic_ir
