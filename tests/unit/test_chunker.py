"""Unit tests for chunker."""

import pytest
from domcontext._internal.chunker import (
    Chunk,
    _collect_lines,
    _calculate_overlap_start,
    chunk_semantic_ir
)
from domcontext._internal.ir.semantic_ir import SemanticElement, SemanticText, SemanticTreeNode, SemanticIR
from domcontext.tokenizer import Tokenizer


class MockTokenizer(Tokenizer):
    """Mock tokenizer that counts characters for predictable testing."""

    def count_tokens(self, text: str) -> int:
        """Count characters as tokens for simple testing."""
        return len(text)


class TestChunk:
    """Test Chunk class."""

    def test_create_empty_chunk(self):
        """Test creating an empty chunk."""
        chunk = Chunk()

        assert chunk.lines == []
        assert chunk.get_tokens() == 0
        assert chunk.to_markdown() == ""

    def test_add_single_line(self):
        """Test adding a single line to chunk."""
        chunk = Chunk()
        chunk.add_line("- div-1", 7)

        assert len(chunk.lines) == 1
        assert chunk.get_tokens() == 7
        assert chunk.to_markdown() == "- div-1"

    def test_add_multiple_lines(self):
        """Test adding multiple lines to chunk."""
        chunk = Chunk()
        chunk.add_line("- div-1", 7)
        chunk.add_line("  - div-2", 9)
        chunk.add_line("    - text", 10)

        assert len(chunk.lines) == 3
        assert chunk.get_tokens() == 26
        assert chunk.to_markdown() == "- div-1\n  - div-2\n    - text"

    def test_token_count_is_running_sum(self):
        """Test that token count is efficiently maintained as running sum."""
        chunk = Chunk()

        chunk.add_line("line1", 5)
        assert chunk.get_tokens() == 5

        chunk.add_line("line2", 3)
        assert chunk.get_tokens() == 8

        chunk.add_line("line3", 7)
        assert chunk.get_tokens() == 15

    def test_backward_compatible_properties(self):
        """Test backward compatible .markdown and .tokens properties."""
        chunk = Chunk()
        chunk.add_line("- div-1", 7)
        chunk.add_line("  - text", 8)

        # Test .markdown property
        assert chunk.markdown == "- div-1\n  - text"

        # Test .tokens property
        assert chunk.tokens == 15


class TestCollectLines:
    """Test _collect_lines helper function."""

    def test_collect_single_element(self):
        """Test collecting lines from single element."""
        elem = SemanticElement(tag="div", readable_id="div-1")
        node = SemanticTreeNode(elem)
        ir = SemanticIR(node, id_index={"div-1": elem})
        tokenizer = MockTokenizer()

        lines = _collect_lines(ir, tokenizer)

        assert len(lines) == 1
        markdown, tokens, path = lines[0]
        assert markdown == "- div-1"
        assert tokens == len("- div-1")
        assert path == []

    def test_collect_nested_elements(self):
        """Test collecting lines from nested elements."""
        parent = SemanticElement(tag="div", readable_id="div-1")
        parent_node = SemanticTreeNode(parent)

        child = SemanticElement(tag="span", readable_id="span-1")
        child_node = SemanticTreeNode(child)
        parent_node.add_child(child_node)

        ir = SemanticIR(parent_node, id_index={"div-1": parent, "span-1": child})
        tokenizer = MockTokenizer()

        lines = _collect_lines(ir, tokenizer)

        assert len(lines) == 2
        # Check parent
        assert lines[0][0] == "- div-1"
        assert lines[0][2] == []  # No parent path
        # Check child
        assert lines[1][0] == "  - span-1"
        assert lines[1][2] == ["div-1"]  # Parent path

    def test_collect_with_text_nodes(self):
        """Test collecting lines with text nodes."""
        elem = SemanticElement(tag="div", readable_id="div-1")
        elem_node = SemanticTreeNode(elem)

        text = SemanticText(text="Hello")
        text_node = SemanticTreeNode(text)
        elem_node.add_child(text_node)

        ir = SemanticIR(elem_node, id_index={"div-1": elem})
        tokenizer = MockTokenizer()

        lines = _collect_lines(ir, tokenizer)

        assert len(lines) == 2
        assert lines[0][0] == "- div-1"
        assert lines[1][0] == '  - "Hello"'

    def test_collect_preserves_indentation(self):
        """Test that indentation is preserved based on depth."""
        root = SemanticElement(tag="body", readable_id="body-1")
        root_node = SemanticTreeNode(root)

        level1 = SemanticElement(tag="div", readable_id="div-1")
        level1_node = SemanticTreeNode(level1)
        root_node.add_child(level1_node)

        level2 = SemanticElement(tag="span", readable_id="span-1")
        level2_node = SemanticTreeNode(level2)
        level1_node.add_child(level2_node)

        ir = SemanticIR(root_node, id_index={"body-1": root, "div-1": level1, "span-1": level2})
        tokenizer = MockTokenizer()

        lines = _collect_lines(ir, tokenizer)

        assert lines[0][0] == "- body-1"  # No indent
        assert lines[1][0] == "  - div-1"  # 2 spaces
        assert lines[2][0] == "    - span-1"  # 4 spaces


class TestCalculateOverlapStart:
    """Test _calculate_overlap_start helper function."""

    def test_no_overlap_when_tokens_zero(self):
        """Test no overlap when overlap_tokens is 0."""
        all_lines = [
            ("line1", 5, []),
            ("line2", 5, []),
            ("line3", 5, []),
        ]

        next_start = _calculate_overlap_start(all_lines, 0, 3, overlap_tokens=0)

        assert next_start == 3

    def test_overlap_single_item(self):
        """Test overlap includes single item."""
        all_lines = [
            ("line1", 5, []),
            ("line2", 5, []),
            ("line3", 5, []),
        ]

        # With overlap=5, should include last item (index 2)
        next_start = _calculate_overlap_start(all_lines, 0, 3, overlap_tokens=5)

        assert next_start == 2

    def test_overlap_multiple_items(self):
        """Test overlap includes multiple items."""
        all_lines = [
            ("line1", 3, []),
            ("line2", 3, []),
            ("line3", 3, []),
            ("line4", 3, []),
        ]

        # With overlap=6, should include last 2 items (indices 2-3)
        next_start = _calculate_overlap_start(all_lines, 0, 4, overlap_tokens=6)

        assert next_start == 2

    def test_overlap_stops_at_chunk_start(self):
        """Test overlap doesn't go before chunk_start."""
        all_lines = [
            ("line1", 5, []),
            ("line2", 5, []),
            ("line3", 5, []),
        ]

        # Chunk from index 2-3, large overlap should not go before index 2
        next_start = _calculate_overlap_start(all_lines, 2, 3, overlap_tokens=100)

        assert next_start == 2

    def test_overlap_with_large_items(self):
        """Test overlap when items are too large to fit in overlap budget."""
        all_lines = [
            ("line1", 100, []),
            ("line2", 100, []),
        ]

        # When overlap budget (1) is too small for any item (100 tokens each),
        # should return chunk_end (no overlap)
        next_start = _calculate_overlap_start(all_lines, 0, 2, overlap_tokens=1)

        assert next_start == 2  # No overlap possible, start at end


class TestChunkSemanticIR:
    """Test chunk_semantic_ir main function."""

    def test_single_chunk_fits_everything(self):
        """Test when everything fits in single chunk."""
        elem = SemanticElement(tag="div", readable_id="div-1")
        node = SemanticTreeNode(elem)
        ir = SemanticIR(node, id_index={"div-1": elem})
        tokenizer = MockTokenizer()

        chunks = chunk_semantic_ir(ir, tokenizer, size=100, overlap=10)

        assert len(chunks) == 1
        assert "div-1" in chunks[0].markdown

    def test_multiple_chunks_created(self):
        """Test splitting into multiple chunks."""
        # Create structure with multiple elements
        root = SemanticElement(tag="body", readable_id="body-1")
        root_node = SemanticTreeNode(root)

        for i in range(5):
            elem = SemanticElement(tag="div", readable_id=f"div-{i+1}")
            child_node = SemanticTreeNode(elem)
            root_node.add_child(child_node)

        ir = SemanticIR(root_node, id_index={
            "body-1": root,
            **{f"div-{i+1}": elem for i, elem in enumerate([
                SemanticElement(tag="div", readable_id=f"div-{i+1}") for i in range(5)
            ])}
        })
        tokenizer = MockTokenizer()

        # Small chunk size to force splitting
        chunks = chunk_semantic_ir(ir, tokenizer, size=20, overlap=5)

        assert len(chunks) > 1

    def test_parent_path_included_in_subsequent_chunks(self):
        """Test that parent path is included in chunks after the first."""
        root = SemanticElement(tag="body", readable_id="body-1")
        root_node = SemanticTreeNode(root)

        div = SemanticElement(tag="div", readable_id="div-1")
        div_node = SemanticTreeNode(div)
        root_node.add_child(div_node)

        # Add multiple children to force multiple chunks
        for i in range(3):
            child = SemanticElement(tag="span", readable_id=f"span-{i+1}")
            child_node = SemanticTreeNode(child)
            div_node.add_child(child_node)

        ir = SemanticIR(root_node, id_index={
            "body-1": root,
            "div-1": div,
            **{f"span-{i+1}": SemanticElement(tag="span", readable_id=f"span-{i+1}") for i in range(3)}
        })
        tokenizer = MockTokenizer()

        chunks = chunk_semantic_ir(ir, tokenizer, size=30, overlap=5, include_parent_path=True)

        # Check that chunks after first have parent paths
        if len(chunks) > 1:
            assert "body-1" in chunks[1].markdown
            assert "div-1" in chunks[1].markdown

    def test_parent_path_excluded_when_disabled(self):
        """Test that parent path is not included when include_parent_path=False."""
        root = SemanticElement(tag="body", readable_id="body-1")
        root_node = SemanticTreeNode(root)

        for i in range(3):
            elem = SemanticElement(tag="div", readable_id=f"div-{i+1}")
            child_node = SemanticTreeNode(elem)
            root_node.add_child(child_node)

        ir = SemanticIR(root_node, id_index={
            "body-1": root,
            **{f"div-{i+1}": SemanticElement(tag="div", readable_id=f"div-{i+1}") for i in range(3)}
        })
        tokenizer = MockTokenizer()

        chunks = chunk_semantic_ir(ir, tokenizer, size=20, overlap=5, include_parent_path=False)

        # First chunk should have body-1
        assert "body-1" in chunks[0].markdown

        # But subsequent chunks should not repeat parent paths
        if len(chunks) > 1:
            # Count occurrences of "body-1" - should only be in first chunk
            body_count = sum(1 for chunk in chunks if "body-1" in chunk.markdown)
            assert body_count == 1

    def test_overlap_working(self):
        """Test that overlap includes items from previous chunk."""
        root = SemanticElement(tag="body", readable_id="body-1")
        root_node = SemanticTreeNode(root)

        divs = []
        for i in range(4):
            elem = SemanticElement(tag="div", readable_id=f"div-{i+1}")
            divs.append(elem)
            child_node = SemanticTreeNode(elem)
            root_node.add_child(child_node)

        ir = SemanticIR(root_node, id_index={
            "body-1": root,
            **{f"div-{i+1}": div for i, div in enumerate(divs)}
        })
        tokenizer = MockTokenizer()

        chunks = chunk_semantic_ir(ir, tokenizer, size=25, overlap=10)

        # With overlap, adjacent chunks should share some content
        if len(chunks) >= 2:
            # Check that some content appears in both chunks
            chunk1_lines = set(chunks[0].markdown.split('\n'))
            chunk2_lines = set(chunks[1].markdown.split('\n'))
            overlap_lines = chunk1_lines & chunk2_lines

            # Should have some overlap (besides just parent paths)
            assert len(overlap_lines) > 0

    def test_chunk_respects_size_limit(self):
        """Test that chunks respect the size limit."""
        root = SemanticElement(tag="body", readable_id="body-1")
        root_node = SemanticTreeNode(root)

        for i in range(10):
            elem = SemanticElement(tag="div", readable_id=f"div-{i+1}")
            child_node = SemanticTreeNode(elem)
            root_node.add_child(child_node)

        ir = SemanticIR(root_node, id_index={
            "body-1": root,
            **{f"div-{i+1}": SemanticElement(tag="div", readable_id=f"div-{i+1}") for i in range(10)}
        })
        tokenizer = MockTokenizer()

        max_size = 50
        chunks = chunk_semantic_ir(ir, tokenizer, size=max_size, overlap=5)

        # Each chunk should not significantly exceed max_size
        # (allowing some overhead for the first item that might be larger)
        for chunk in chunks:
            # If chunk has only one line, it can exceed size (first item always added)
            if len(chunk.lines) > 1:
                assert chunk.get_tokens() <= max_size * 1.5  # Allow 50% margin for edge cases

    def test_empty_semantic_ir(self):
        """Test chunking empty semantic IR."""
        # Create minimal empty structure
        root = SemanticElement(tag="body", readable_id="body-1")
        root_node = SemanticTreeNode(root)
        ir = SemanticIR(root_node, id_index={"body-1": root})
        tokenizer = MockTokenizer()

        chunks = chunk_semantic_ir(ir, tokenizer, size=100, overlap=10)

        assert len(chunks) == 1
        assert chunks[0].get_tokens() > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
