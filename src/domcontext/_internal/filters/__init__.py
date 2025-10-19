"""Filtering passes for IR trees."""

from .semantic_pass import semantic_pass
from .visibility_pass import visibility_pass

__all__ = ["visibility_pass", "semantic_pass"]
