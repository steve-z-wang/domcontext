"""Unit tests for tokenizers."""

import pytest

from domcontext.tokenizer import TiktokenTokenizer, Tokenizer


class MockTokenizer(Tokenizer):
    """Mock tokenizer for testing abstract interface."""

    def count_tokens(self, text: str) -> int:
        """Simple word-based tokenizer for testing."""
        return len(text.split())


class TestTokenizerInterface:
    """Test Tokenizer abstract interface."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that abstract Tokenizer cannot be instantiated."""
        with pytest.raises(TypeError):
            Tokenizer()

    def test_can_implement_interface(self):
        """Test that Tokenizer can be subclassed."""
        tokenizer = MockTokenizer()

        count = tokenizer.count_tokens("hello world")

        assert count == 2


class TestTiktokenTokenizer:
    """Test TiktokenTokenizer implementation."""

    def test_creates_with_default_encoding(self):
        """Test creating tokenizer with default encoding."""
        tokenizer = TiktokenTokenizer()

        assert tokenizer is not None
        assert hasattr(tokenizer, "_enc")

    def test_creates_with_custom_encoding(self):
        """Test creating tokenizer with custom encoding."""
        tokenizer = TiktokenTokenizer(encoding="cl100k_base")

        assert tokenizer is not None

    def test_counts_simple_text(self):
        """Test counting tokens in simple text."""
        tokenizer = TiktokenTokenizer()

        count = tokenizer.count_tokens("Hello world")

        assert count > 0
        assert isinstance(count, int)

    def test_counts_empty_string(self):
        """Test counting tokens in empty string."""
        tokenizer = TiktokenTokenizer()

        count = tokenizer.count_tokens("")

        assert count == 0

    def test_counts_longer_text(self):
        """Test counting tokens in longer text."""
        tokenizer = TiktokenTokenizer()
        text = "The quick brown fox jumps over the lazy dog. This is a test sentence."

        count = tokenizer.count_tokens(text)

        # Should be reasonable number of tokens
        assert count > 10
        assert count < 100

    def test_counts_special_characters(self):
        """Test counting tokens with special characters."""
        tokenizer = TiktokenTokenizer()

        count = tokenizer.count_tokens("Hello, world! <tag>")

        assert count > 0

    def test_counts_multiline_text(self):
        """Test counting tokens in multiline text."""
        tokenizer = TiktokenTokenizer()
        text = """Line 1
        Line 2
        Line 3"""

        count = tokenizer.count_tokens(text)

        assert count > 0

    def test_consistent_results(self):
        """Test that counting same text gives consistent results."""
        tokenizer = TiktokenTokenizer()
        text = "Consistent test"

        count1 = tokenizer.count_tokens(text)
        count2 = tokenizer.count_tokens(text)

        assert count1 == count2

    def test_different_texts_different_counts(self):
        """Test that different texts give different counts."""
        tokenizer = TiktokenTokenizer()

        count1 = tokenizer.count_tokens("short")
        count2 = tokenizer.count_tokens("This is a much longer sentence with more tokens")

        assert count2 > count1

    def test_counts_html_like_content(self):
        """Test counting tokens in HTML-like content."""
        tokenizer = TiktokenTokenizer()
        html = '<button type="submit">Click me</button>'

        count = tokenizer.count_tokens(html)

        assert count > 0

    def test_counts_markdown_like_content(self):
        """Test counting tokens in markdown-like content."""
        tokenizer = TiktokenTokenizer()
        markdown = """- item-1
  - subitem-1
- item-2"""

        count = tokenizer.count_tokens(markdown)

        assert count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
