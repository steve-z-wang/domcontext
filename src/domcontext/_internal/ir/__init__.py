"""Internal Representation (IR) for DOM trees."""

from .dom_ir import DomElement, DomText, DomTreeNode, DomIR
from .semantic_ir import SemanticElement, SemanticText, SemanticTreeNode, SemanticIR

__all__ = [
    'DomElement',
    'DomText',
    'DomTreeNode',
    'DomIR',
    'SemanticElement',
    'SemanticText',
    'SemanticTreeNode',
    'SemanticIR'
]
