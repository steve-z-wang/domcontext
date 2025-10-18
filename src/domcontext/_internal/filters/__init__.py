"""Filtering passes for IR trees."""

from .visibility_pass import visibility_pass
from .semantic_pass import semantic_pass

__all__ = ["visibility_pass", "semantic_pass"]
