"""Smoke test to verify setup is working."""

import pytest
from domcontext import DomContext, DomNode, Tokenizer, TiktokenTokenizer, Chunk


def test_imports():
    """Test that all public API imports work."""
    assert DomContext is not None
    assert DomNode is not None
    assert Tokenizer is not None
    assert TiktokenTokenizer is not None
    assert Chunk is not None


def test_simple_parsing(simple_html):
    """Test basic HTML parsing works."""
    context = DomContext.from_html(simple_html)

    assert context is not None
    assert context.markdown is not None
    assert context.tokens > 0
    assert len(context.elements()) > 0


def test_tokenizer():
    """Test default tokenizer works."""
    tokenizer = TiktokenTokenizer()
    count = tokenizer.count_tokens("Hello world")

    assert count > 0
    assert isinstance(count, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
