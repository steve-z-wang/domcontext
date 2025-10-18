"""Tokenizer interface for counting tokens."""

from abc import ABC, abstractmethod


class Tokenizer(ABC):
    """Abstract base class for tokenizers."""

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        pass


class TiktokenTokenizer(Tokenizer):
    """Default tokenizer using tiktoken (OpenAI's tokenizer).

    Good approximation for most LLMs including GPT, Claude, Gemini.
    """

    def __init__(self, encoding: str = "cl100k_base"):
        """Initialize tiktoken tokenizer.

        Args:
            encoding: Tiktoken encoding name (default: cl100k_base for GPT-4/3.5)
        """
        import tiktoken
        self._enc = tiktoken.get_encoding(encoding)

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        return len(self._enc.encode(text))
