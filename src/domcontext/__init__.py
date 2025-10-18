"""domcontext - Parse DOM trees into clean, LLM-friendly context."""

from .dom_context import DomContext
from .dom_node import DomNode
from ._internal.chunker import Chunk
from .tokenizer import Tokenizer, TiktokenTokenizer

__version__ = "0.1.0"

__all__ = [
    'DomContext',
    'DomNode',
    'Chunk',
    'Tokenizer',
    'TiktokenTokenizer',
]
