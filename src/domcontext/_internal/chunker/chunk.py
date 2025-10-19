"""Chunk container for accumulating text pieces."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Chunk:
    """Simple chunk container - just accumulates text and tracks tokens.

    No line-level operations - just stores text pieces.
    """

    text_pieces: List[str] = field(default_factory=list)
    _total_tokens: int = field(default=0, init=False, repr=False)

    def add_text(self, text: str, tokens: int):
        """Add a text piece with its token count."""
        self.text_pieces.append(text)
        self._total_tokens += tokens

    def get_tokens(self) -> int:
        """Get total tokens (O(1))."""
        return self._total_tokens

    def to_markdown(self) -> str:
        """Convert to markdown string."""
        return "".join(self.text_pieces)  # Just concatenate (newlines already in text)

    @property
    def markdown(self) -> str:
        """Backward compatibility: get markdown as property."""
        return self.to_markdown()

    @property
    def tokens(self) -> int:
        """Backward compatibility: get tokens as property."""
        return self.get_tokens()
