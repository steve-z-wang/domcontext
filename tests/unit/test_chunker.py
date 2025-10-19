"""Unit tests for chunker."""

import pytest

from domcontext._internal.chunker import Chunk, chunk_semantic_ir
from domcontext._internal.ir.semantic_ir import (
    SemanticElement,
    SemanticIR,
    SemanticText,
    SemanticTreeNode,
)
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

        assert chunk.text_pieces == []
        assert chunk.get_tokens() == 0
        assert chunk.to_markdown() == ""

    def test_add_single_text(self):
        """Test adding a single text piece to chunk."""
        chunk = Chunk()
        chunk.add_text("- div-1\n", 8)

        assert len(chunk.text_pieces) == 1
        assert chunk.get_tokens() == 8
        assert chunk.to_markdown() == "- div-1\n"

    def test_add_multiple_texts(self):
        """Test adding multiple text pieces to chunk."""
        chunk = Chunk()
        chunk.add_text("- div-1\n", 8)
        chunk.add_text("  - div-2\n", 11)
        chunk.add_text("    - text\n", 12)

        assert len(chunk.text_pieces) == 3
        assert chunk.get_tokens() == 31
        assert chunk.to_markdown() == "- div-1\n  - div-2\n    - text\n"

    def test_token_count_is_running_sum(self):
        """Test that token count is efficiently maintained as running sum."""
        chunk = Chunk()

        chunk.add_text("line1\n", 6)
        assert chunk.get_tokens() == 6

        chunk.add_text("line2\n", 6)
        assert chunk.get_tokens() == 12

        chunk.add_text("line3\n", 6)
        assert chunk.get_tokens() == 18

    def test_backward_compatible_properties(self):
        """Test backward compatible .markdown and .tokens properties."""
        chunk = Chunk()
        chunk.add_text("- div-1\n", 8)
        chunk.add_text("  - text\n", 10)

        # Test .markdown property
        assert chunk.markdown == "- div-1\n  - text\n"

        # Test .tokens property
        assert chunk.tokens == 18


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

    def test_element_with_attributes_splits(self):
        """Test that elements with many attributes get split properly."""
        elem = SemanticElement(
            tag="button",
            readable_id="button-1",
            semantic_attributes={
                "type": "submit",
                "class": "btn-primary btn-large",
                "aria-label": "Submit form",
                "data-action": "submit",
            },
        )
        node = SemanticTreeNode(elem)
        ir = SemanticIR(node, id_index={"button-1": elem})
        tokenizer = MockTokenizer()

        # Small size to force splitting
        chunks = chunk_semantic_ir(ir, tokenizer, size=50, overlap=10)

        assert len(chunks) > 1
        # Check for continuation markers
        markdown = "".join(c.markdown for c in chunks)
        assert "..." in markdown

    def test_long_text_splits(self):
        """Test that long text gets split by words."""
        elem = SemanticElement(tag="p", readable_id="p-1")
        elem_node = SemanticTreeNode(elem)

        text = SemanticText(
            text="This is a very long text that should be split into multiple chunks"
        )
        text_node = SemanticTreeNode(text)
        elem_node.add_child(text_node)

        ir = SemanticIR(elem_node, id_index={"p-1": elem})
        tokenizer = MockTokenizer()

        # Small size to force text splitting
        chunks = chunk_semantic_ir(ir, tokenizer, size=60, overlap=5)

        assert len(chunks) > 1
        # Check for text continuation markers
        markdown = "".join(c.markdown for c in chunks)
        assert '..."' in markdown or '"...' in markdown

    def test_multiple_chunks_created(self):
        """Test splitting into multiple chunks."""
        # Create structure with multiple elements
        root = SemanticElement(tag="body", readable_id="body-1")
        root_node = SemanticTreeNode(root)

        for i in range(5):
            elem = SemanticElement(tag="div", readable_id=f"div-{i+1}")
            child_node = SemanticTreeNode(elem)
            root_node.add_child(child_node)

        ir = SemanticIR(
            root_node,
            id_index={
                "body-1": root,
                **{
                    f"div-{i+1}": SemanticElement(tag="div", readable_id=f"div-{i+1}")
                    for i in range(5)
                },
            },
        )
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

        ir = SemanticIR(
            root_node,
            id_index={
                "body-1": root,
                "div-1": div,
                **{
                    f"span-{i+1}": SemanticElement(tag="span", readable_id=f"span-{i+1}")
                    for i in range(3)
                },
            },
        )
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

        ir = SemanticIR(
            root_node,
            id_index={
                "body-1": root,
                **{
                    f"div-{i+1}": SemanticElement(tag="div", readable_id=f"div-{i+1}")
                    for i in range(3)
                },
            },
        )
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

        ir = SemanticIR(
            root_node,
            id_index={"body-1": root, **{f"div-{i+1}": div for i, div in enumerate(divs)}},
        )
        tokenizer = MockTokenizer()

        chunks = chunk_semantic_ir(ir, tokenizer, size=25, overlap=10)

        # With overlap, adjacent chunks should share some content
        if len(chunks) >= 2:
            # Check that some content appears in both chunks
            chunk1_lines = set(chunks[0].markdown.split("\n"))
            chunk2_lines = set(chunks[1].markdown.split("\n"))
            overlap_lines = chunk1_lines & chunk2_lines

            # Should have some overlap (besides just parent paths)
            assert len(overlap_lines) > 0

    def test_chunk_respects_size_limit(self):
        """Test that chunks respect the size limit (with some tolerance for forced adds)."""
        root = SemanticElement(tag="body", readable_id="body-1")
        root_node = SemanticTreeNode(root)

        for i in range(10):
            elem = SemanticElement(tag="div", readable_id=f"div-{i+1}")
            child_node = SemanticTreeNode(elem)
            root_node.add_child(child_node)

        ir = SemanticIR(
            root_node,
            id_index={
                "body-1": root,
                **{
                    f"div-{i+1}": SemanticElement(tag="div", readable_id=f"div-{i+1}")
                    for i in range(10)
                },
            },
        )
        tokenizer = MockTokenizer()

        max_size = 50
        chunks = chunk_semantic_ir(ir, tokenizer, size=max_size, overlap=5)

        # Each chunk should not significantly exceed max_size
        # (allowing overhead for forced adds and parent paths)
        for chunk in chunks:
            # Allow reasonable margin for parent paths and forced adds
            assert chunk.get_tokens() <= max_size * 2

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

    def test_continuation_markers_correct(self):
        """Test that continuation markers are added correctly."""
        elem = SemanticElement(
            tag="button",
            readable_id="btn-1",
            semantic_attributes={"type": "submit", "class": "btn-primary", "aria-label": "Submit"},
        )
        node = SemanticTreeNode(elem)
        ir = SemanticIR(node, id_index={"btn-1": elem})
        tokenizer = MockTokenizer()

        # Force splitting
        chunks = chunk_semantic_ir(ir, tokenizer, size=40, overlap=5)

        if len(chunks) > 1:
            # First chunk should end with "...)"
            assert "...)" in chunks[0].markdown

            # Middle chunks should have "(... " and " ...)"
            for i in range(1, len(chunks) - 1):
                assert "..." in chunks[i].markdown

            # Last chunk should have "(... " but not end with "...)"
            assert "..." in chunks[-1].markdown
            # Last line should end with just ")"
            last_line = chunks[-1].markdown.strip().split("\n")[-1]
            assert last_line.endswith(")")
            assert not last_line.endswith("...)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
