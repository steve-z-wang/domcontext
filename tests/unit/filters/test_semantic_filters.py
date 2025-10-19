"""Unit tests for semantic filter passes."""

import pytest

from domcontext._internal.filters.semantic.collapse_wrappers import collapse_wrappers_pass
from domcontext._internal.filters.semantic.convert import convert_to_semantic_pass
from domcontext._internal.filters.semantic.filter_attributes import (
    SEMANTIC_ATTRIBUTES,
    filter_by_attributes_pass,
)
from domcontext._internal.filters.semantic.filter_empty import (
    INTERACTIVE_TAGS,
    filter_empty_nodes_pass,
)
from domcontext._internal.filters.semantic.generate_ids import generate_ids_pass
from domcontext._internal.ir.dom_ir import DomElement, DomText, DomTreeNode
from domcontext._internal.ir.semantic_ir import SemanticElement, SemanticText, SemanticTreeNode


class TestConvertToSemantic:
    """Test convert_to_semantic_pass."""

    def test_convert_simple_element(self):
        """Test converting simple element node."""
        dom_elem = DomElement(tag="div", attributes={"class": "test"})
        dom_node = DomTreeNode(data=dom_elem)

        semantic_node = convert_to_semantic_pass(dom_node)

        assert isinstance(semantic_node.data, SemanticElement)
        assert semantic_node.data.tag == "div"
        assert semantic_node.data.semantic_attributes == {"class": "test"}
        assert semantic_node.data.dom_tree_node is dom_node

    def test_convert_text_node(self):
        """Test converting text node."""
        dom_text = DomText(text="Hello World")
        dom_node = DomTreeNode(data=dom_text)

        semantic_node = convert_to_semantic_pass(dom_node)

        assert isinstance(semantic_node.data, SemanticText)
        assert semantic_node.data.text == "Hello World"
        assert semantic_node.data.dom_tree_node is dom_node

    def test_convert_with_children(self):
        """Test converting tree with children."""
        dom_div = DomElement(tag="div")
        dom_p = DomElement(tag="p")
        dom_text = DomText(text="Content")

        dom_div_node = DomTreeNode(data=dom_div)
        dom_p_node = DomTreeNode(data=dom_p)
        dom_text_node = DomTreeNode(data=dom_text)

        dom_div_node.add_child(dom_p_node)
        dom_p_node.add_child(dom_text_node)

        semantic_node = convert_to_semantic_pass(dom_div_node)

        assert semantic_node.data.tag == "div"
        assert len(semantic_node.children) == 1
        assert semantic_node.children[0].data.tag == "p"
        assert len(semantic_node.children[0].children) == 1
        assert semantic_node.children[0].children[0].data.text == "Content"

    def test_preserves_all_attributes(self):
        """Test that all attributes are preserved (filtering happens later)."""
        dom_elem = DomElement(
            tag="input", attributes={"type": "text", "class": "form-control", "data-test": "foo"}
        )
        dom_node = DomTreeNode(data=dom_elem)

        semantic_node = convert_to_semantic_pass(dom_node)

        # All attributes should be copied
        assert semantic_node.data.semantic_attributes["type"] == "text"
        assert semantic_node.data.semantic_attributes["class"] == "form-control"
        assert semantic_node.data.semantic_attributes["data-test"] == "foo"


class TestFilterByAttributes:
    """Test filter_by_attributes_pass."""

    def test_keeps_semantic_attributes(self):
        """Test that semantic attributes are kept."""
        semantic_elem = SemanticElement(
            tag="button", semantic_attributes={"type": "submit", "name": "btn"}
        )
        semantic_node = SemanticTreeNode(data=semantic_elem)

        result = filter_by_attributes_pass(semantic_node)

        assert result is not None
        assert result.data.semantic_attributes["type"] == "submit"
        assert result.data.semantic_attributes["name"] == "btn"

    def test_removes_non_semantic_attributes(self):
        """Test that non-semantic attributes are removed."""
        semantic_elem = SemanticElement(
            tag="div", semantic_attributes={"class": "test", "id": "foo", "role": "navigation"}
        )
        semantic_node = SemanticTreeNode(data=semantic_elem)

        result = filter_by_attributes_pass(semantic_node)

        assert result is not None
        # Only role should remain (it's in SEMANTIC_ATTRIBUTES)
        assert result.data.semantic_attributes == {"role": "navigation"}

    def test_keeps_all_semantic_attribute_types(self):
        """Test that all defined semantic attributes are kept."""
        # Test each semantic attribute type
        for attr_name in SEMANTIC_ATTRIBUTES:
            semantic_elem = SemanticElement(tag="div", semantic_attributes={attr_name: "value"})
            semantic_node = SemanticTreeNode(data=semantic_elem)

            result = filter_by_attributes_pass(semantic_node)

            assert result is not None
            assert result.data.semantic_attributes[attr_name] == "value"

    def test_removes_empty_text(self):
        """Test that empty/whitespace-only text is removed."""
        semantic_text = SemanticText(text="   ")
        semantic_node = SemanticTreeNode(data=semantic_text)

        result = filter_by_attributes_pass(semantic_node)

        assert result is None

    def test_keeps_non_empty_text(self):
        """Test that non-empty text is kept."""
        semantic_text = SemanticText(text="Hello")
        semantic_node = SemanticTreeNode(data=semantic_text)

        result = filter_by_attributes_pass(semantic_node)

        assert result is not None
        assert result.data.text == "Hello"

    def test_filters_children_recursively(self):
        """Test that children are filtered recursively."""
        parent = SemanticTreeNode(
            data=SemanticElement(
                tag="div", semantic_attributes={"class": "container"}  # Will be removed
            )
        )
        child_keep = SemanticTreeNode(
            data=SemanticElement(
                tag="button", semantic_attributes={"type": "submit"}  # Will be kept
            )
        )
        child_remove = SemanticTreeNode(data=SemanticText(text="  "))  # Will be removed

        parent.add_child(child_keep)
        parent.add_child(child_remove)

        result = filter_by_attributes_pass(parent)

        assert result is not None
        assert len(result.children) == 1  # Only button kept
        assert result.children[0].data.semantic_attributes == {"type": "submit"}


class TestFilterEmpty:
    """Test filter_empty_nodes_pass."""

    def test_keeps_node_with_attributes(self):
        """Test that nodes with attributes are kept."""
        semantic_elem = SemanticElement(tag="div", semantic_attributes={"role": "navigation"})
        semantic_node = SemanticTreeNode(data=semantic_elem)

        result = filter_empty_nodes_pass(semantic_node)

        assert result is not None

    def test_keeps_node_with_children(self):
        """Test that nodes with children are kept."""
        parent = SemanticTreeNode(data=SemanticElement(tag="div"))
        # Child needs attributes or be interactive to not be filtered
        child = SemanticTreeNode(data=SemanticElement(tag="button"))  # Interactive tag
        parent.add_child(child)

        result = filter_empty_nodes_pass(parent)

        assert result is not None
        assert len(result.children) > 0

    def test_removes_empty_node(self):
        """Test that empty nodes (no attributes, no children) are removed."""
        semantic_elem = SemanticElement(tag="div")
        semantic_node = SemanticTreeNode(data=semantic_elem)

        result = filter_empty_nodes_pass(semantic_node)

        assert result is None

    def test_keeps_interactive_tags_even_when_empty(self):
        """Test that interactive tags are kept even without attributes."""
        for tag_name in INTERACTIVE_TAGS:
            semantic_elem = SemanticElement(tag=tag_name)
            semantic_node = SemanticTreeNode(data=semantic_elem)

            result = filter_empty_nodes_pass(semantic_node)

            assert result is not None, f"Interactive tag {tag_name} should be kept"

    def test_removes_empty_text(self):
        """Test that empty text is removed."""
        semantic_text = SemanticText(text="   ")
        semantic_node = SemanticTreeNode(data=semantic_text)

        result = filter_empty_nodes_pass(semantic_node)

        assert result is None

    def test_keeps_non_empty_text(self):
        """Test that non-empty text is kept."""
        semantic_text = SemanticText(text="Hello")
        semantic_node = SemanticTreeNode(data=semantic_text)

        result = filter_empty_nodes_pass(semantic_node)

        assert result is not None

    def test_filters_children_bottom_up(self):
        """Test that children are filtered bottom-up."""
        # parent (empty) > child (with text)
        parent = SemanticTreeNode(data=SemanticElement(tag="div"))
        child = SemanticTreeNode(data=SemanticElement(tag="p"))
        text = SemanticTreeNode(data=SemanticText(text="Content"))

        parent.add_child(child)
        child.add_child(text)

        result = filter_empty_nodes_pass(parent)

        # Parent should be kept because it has children
        assert result is not None
        assert len(result.children) == 1


class TestCollapseWrappers:
    """Test collapse_wrappers_pass."""

    def test_collapses_single_child_wrapper(self):
        """Test that wrapper with single element child is collapsed."""
        # div (no attrs) > p (with text)
        parent = SemanticTreeNode(data=SemanticElement(tag="div"))
        child = SemanticTreeNode(
            data=SemanticElement(tag="p", semantic_attributes={"role": "note"})
        )

        parent.add_child(child)

        result = collapse_wrappers_pass(parent)

        # Parent should be collapsed, child promoted (returns the processed child)
        assert result.data.tag == "p"
        assert result.data.semantic_attributes["role"] == "note"

    def test_keeps_wrapper_with_attributes(self):
        """Test that wrappers with attributes are not collapsed."""
        parent = SemanticTreeNode(
            data=SemanticElement(tag="div", semantic_attributes={"role": "navigation"})
        )
        child = SemanticTreeNode(data=SemanticElement(tag="p"))

        parent.add_child(child)

        result = collapse_wrappers_pass(parent)

        # Parent should be kept
        assert result.data.tag == "div"
        assert len(result.children) == 1

    def test_keeps_wrapper_with_multiple_children(self):
        """Test that wrappers with multiple children are not collapsed."""
        parent = SemanticTreeNode(data=SemanticElement(tag="div"))
        child1 = SemanticTreeNode(data=SemanticElement(tag="p"))
        child2 = SemanticTreeNode(data=SemanticElement(tag="span"))

        parent.add_child(child1)
        parent.add_child(child2)

        result = collapse_wrappers_pass(parent)

        # Parent should be kept
        assert result.data.tag == "div"
        assert len(result.children) == 2

    def test_keeps_wrapper_with_meaningful_text(self):
        """Test that wrappers with meaningful text are not collapsed."""
        parent = SemanticTreeNode(data=SemanticElement(tag="div"))
        text = SemanticTreeNode(data=SemanticText(text="Content"))
        child = SemanticTreeNode(data=SemanticElement(tag="p"))

        parent.add_child(text)
        parent.add_child(child)

        result = collapse_wrappers_pass(parent)

        # Parent should be kept because of meaningful text
        assert result.data.tag == "div"
        assert len(result.children) == 2

    def test_keeps_text_nodes(self):
        """Test that text nodes are kept."""
        semantic_text = SemanticText(text="Hello")
        semantic_node = SemanticTreeNode(data=semantic_text)

        result = collapse_wrappers_pass(semantic_node)

        assert result is not None
        assert isinstance(result.data, SemanticText)

    def test_collapses_nested_wrappers(self):
        """Test that nested wrappers are collapsed bottom-up."""
        # div (no attrs) > div (no attrs) > p (with attrs)
        grandparent = SemanticTreeNode(data=SemanticElement(tag="div"))
        parent = SemanticTreeNode(data=SemanticElement(tag="div"))
        child = SemanticTreeNode(
            data=SemanticElement(tag="p", semantic_attributes={"role": "note"})
        )

        grandparent.add_child(parent)
        parent.add_child(child)

        result = collapse_wrappers_pass(grandparent)

        # Both wrappers should be collapsed, only p remains
        assert result is not None
        assert result.data.tag == "p"


class TestGenerateIds:
    """Test generate_ids_pass."""

    def test_assigns_ids_to_elements(self):
        """Test that readable IDs are assigned to elements."""
        elem = SemanticElement(tag="button")
        node = SemanticTreeNode(data=elem)

        result_node, id_mapping = generate_ids_pass(node)

        assert elem.readable_id == "button-1"
        assert id_mapping["button-1"] is elem

    def test_increments_counter_per_tag(self):
        """Test that IDs increment per tag type."""
        div1 = SemanticElement(tag="div")
        div2 = SemanticElement(tag="div")
        button1 = SemanticElement(tag="button")

        root = SemanticTreeNode(data=div1)
        child1 = SemanticTreeNode(data=div2)
        child2 = SemanticTreeNode(data=button1)

        root.add_child(child1)
        root.add_child(child2)

        result_node, id_mapping = generate_ids_pass(root)

        assert div1.readable_id == "div-1"
        assert div2.readable_id == "div-2"
        assert button1.readable_id == "button-1"

    def test_builds_complete_id_mapping(self):
        """Test that ID mapping includes all elements."""
        elem1 = SemanticElement(tag="div")
        elem2 = SemanticElement(tag="p")
        elem3 = SemanticElement(tag="span")

        root = SemanticTreeNode(data=elem1)
        child1 = SemanticTreeNode(data=elem2)
        child2 = SemanticTreeNode(data=elem3)

        root.add_child(child1)
        root.add_child(child2)

        result_node, id_mapping = generate_ids_pass(root)

        assert len(id_mapping) == 3
        assert id_mapping["div-1"] is elem1
        assert id_mapping["p-1"] is elem2
        assert id_mapping["span-1"] is elem3

    def test_skips_text_nodes(self):
        """Test that text nodes don't get IDs."""
        elem = SemanticElement(tag="p")
        text = SemanticText(text="Hello")

        root = SemanticTreeNode(data=elem)
        child = SemanticTreeNode(data=text)
        root.add_child(child)

        result_node, id_mapping = generate_ids_pass(root)

        # Only element should get ID
        assert elem.readable_id == "p-1"
        assert len(id_mapping) == 1

    def test_modifies_tree_in_place(self):
        """Test that the original tree is modified in place."""
        elem = SemanticElement(tag="button")
        node = SemanticTreeNode(data=elem)

        result_node, id_mapping = generate_ids_pass(node)

        # Same node returned
        assert result_node is node
        # Original element modified
        assert elem.readable_id is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
