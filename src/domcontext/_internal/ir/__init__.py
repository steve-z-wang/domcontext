"""Internal Representation (IR) for DOM trees."""

from .dom_ir import DomElement, DomIR, DomText, DomTreeNode
from .semantic_ir import SemanticElement, SemanticIR, SemanticText, SemanticTreeNode

__all__ = [
    "DomElement",
    "DomText",
    "DomTreeNode",
    "DomIR",
    "SemanticElement",
    "SemanticText",
    "SemanticTreeNode",
    "SemanticIR",
]
