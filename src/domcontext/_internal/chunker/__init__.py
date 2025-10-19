"""Chunker module for splitting semantic IR into LLM-friendly chunks."""

from .chunk import Chunk
from .chunker import chunk_semantic_ir

__all__ = ["Chunk", "chunk_semantic_ir"]
