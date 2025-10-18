"""Unit tests for visibility filter passes."""

import pytest
from domcontext._internal.ir.dom_ir import DomElement, DomText, DomTreeNode, BoundingBox
from domcontext._internal.filters.visibility.non_visible_tags import filter_non_visible_tags_pass
from domcontext._internal.filters.visibility.css_hidden import filter_css_hidden_pass
from domcontext._internal.filters.visibility.zero_dimensions import filter_zero_dimensions_pass
from domcontext._internal.filters.visibility.utils import parse_inline_style, NON_VISIBLE_TAGS


class TestNonVisibleTagsFilter:
    """Test filter_non_visible_tags_pass."""

    def test_keeps_visible_element(self):
        """Test that visible elements are kept."""
        div = DomTreeNode(data=DomElement(tag="div"))

        result = filter_non_visible_tags_pass(div)

        assert result is not None
        assert isinstance(result.data, DomElement)
        assert result.data.tag == "div"

    def test_removes_script_tag(self):
        """Test that script tags are removed."""
        script = DomTreeNode(data=DomElement(tag="script"))

        result = filter_non_visible_tags_pass(script)

        assert result is None

    def test_removes_style_tag(self):
        """Test that style tags are removed."""
        style = DomTreeNode(data=DomElement(tag="style"))

        result = filter_non_visible_tags_pass(style)

        assert result is None

    def test_removes_head_tag(self):
        """Test that head tags are removed."""
        head = DomTreeNode(data=DomElement(tag="head"))

        result = filter_non_visible_tags_pass(head)

        assert result is None

    def test_removes_all_non_visible_tags(self):
        """Test that all NON_VISIBLE_TAGS are removed."""
        for tag_name in NON_VISIBLE_TAGS:
            node = DomTreeNode(data=DomElement(tag=tag_name))
            result = filter_non_visible_tags_pass(node)
            assert result is None, f"Tag {tag_name} should be removed"

    def test_keeps_text_nodes(self):
        """Test that text nodes are always kept."""
        text = DomTreeNode(data=DomText(text="Hello World"))

        result = filter_non_visible_tags_pass(text)

        assert result is not None
        assert isinstance(result.data, DomText)
        assert result.data.text == "Hello World"

    def test_filters_children_recursively(self):
        """Test that children are filtered recursively."""
        # Create tree: div > [script, p]
        div = DomTreeNode(data=DomElement(tag="div"))
        script = DomTreeNode(data=DomElement(tag="script"))
        p = DomTreeNode(data=DomElement(tag="p"))

        div.add_child(script)
        div.add_child(p)

        result = filter_non_visible_tags_pass(div)

        assert result is not None
        assert result.data.tag == "div"
        # Only p should remain (script filtered out)
        element_children = result.get_element_children()
        assert len(element_children) == 1
        assert element_children[0].data.tag == "p"

    def test_nested_non_visible_tags(self):
        """Test filtering deeply nested non-visible tags."""
        # Create tree: html > head > [title, meta]
        html = DomTreeNode(data=DomElement(tag="html"))
        head = DomTreeNode(data=DomElement(tag="head"))
        title = DomTreeNode(data=DomElement(tag="title"))
        meta = DomTreeNode(data=DomElement(tag="meta"))

        html.add_child(head)
        head.add_child(title)
        head.add_child(meta)

        result = filter_non_visible_tags_pass(html)

        assert result is not None
        assert result.data.tag == "html"
        # Head and all children should be filtered
        assert len(result.children) == 0

    def test_preserves_visible_structure(self):
        """Test that visible element structure is preserved."""
        # Create tree: body > div > p > text
        body = DomTreeNode(data=DomElement(tag="body"))
        div = DomTreeNode(data=DomElement(tag="div"))
        p = DomTreeNode(data=DomElement(tag="p"))
        text = DomTreeNode(data=DomText(text="Content"))

        body.add_child(div)
        div.add_child(p)
        p.add_child(text)

        result = filter_non_visible_tags_pass(body)

        assert result is not None
        assert result.data.tag == "body"

        div_children = result.get_element_children()
        assert len(div_children) == 1
        assert div_children[0].data.tag == "div"

        p_children = div_children[0].get_element_children()
        assert len(p_children) == 1
        assert p_children[0].data.tag == "p"

        text_children = p_children[0].get_text_children()
        assert len(text_children) == 1
        assert text_children[0].data.text == "Content"

    def test_mixed_visible_and_non_visible_children(self):
        """Test filtering tree with mix of visible and non-visible children."""
        # Create tree: html > [head, body]
        # head should be removed, body should remain
        html = DomTreeNode(data=DomElement(tag="html"))
        head = DomTreeNode(data=DomElement(tag="head"))
        body = DomTreeNode(data=DomElement(tag="body"))

        html.add_child(head)
        html.add_child(body)

        result = filter_non_visible_tags_pass(html)

        assert result is not None
        assert result.data.tag == "html"
        element_children = result.get_element_children()
        assert len(element_children) == 1
        assert element_children[0].data.tag == "body"

    def test_creates_new_tree_nodes(self):
        """Test that new tree nodes are created (not mutating original)."""
        div = DomTreeNode(data=DomElement(tag="div"))
        p = DomTreeNode(data=DomElement(tag="p"))
        div.add_child(p)

        result = filter_non_visible_tags_pass(div)

        # Should be different tree node instances
        assert result is not div
        assert result.get_element_children()[0] is not p
        # But same data
        assert result.data is div.data


class TestVisibilityUtils:
    """Test visibility utility functions."""

    def test_parse_inline_style_simple(self):
        """Test parsing simple inline style."""
        style = "display: none"

        result = parse_inline_style(style)

        assert result["display"] == "none"

    def test_parse_inline_style_multiple(self):
        """Test parsing multiple style declarations."""
        style = "display: none; visibility: hidden; color: red"

        result = parse_inline_style(style)

        assert result["display"] == "none"
        assert result["visibility"] == "hidden"
        assert result["color"] == "red"

    def test_parse_inline_style_trailing_semicolon(self):
        """Test parsing style with trailing semicolon."""
        style = "display: none;"

        result = parse_inline_style(style)

        assert result["display"] == "none"

    def test_parse_inline_style_whitespace(self):
        """Test parsing style with extra whitespace."""
        style = "  display : none  ;  visibility : hidden  "

        result = parse_inline_style(style)

        assert result["display"] == "none"
        assert result["visibility"] == "hidden"

    def test_parse_inline_style_case_insensitive(self):
        """Test that parsing is case-insensitive."""
        style = "DISPLAY: NONE; Visibility: Hidden"

        result = parse_inline_style(style)

        assert result["display"] == "none"
        assert result["visibility"] == "hidden"

    def test_parse_inline_style_empty(self):
        """Test parsing empty style string."""
        style = ""

        result = parse_inline_style(style)

        assert result == {}

    def test_parse_inline_style_none(self):
        """Test parsing None style."""
        style = None

        result = parse_inline_style(style)

        assert result == {}

    def test_parse_inline_style_malformed(self):
        """Test parsing malformed style (no colon)."""
        style = "invalid_property"

        result = parse_inline_style(style)

        # Should not crash, just skip invalid declarations
        assert result == {}

    def test_parse_inline_style_with_value_containing_colon(self):
        """Test parsing style value that contains colon (like URLs)."""
        style = "background: url(http://example.com/image.png)"

        result = parse_inline_style(style)

        # Should keep everything after first colon as value
        assert result["background"] == "url(http://example.com/image.png)"


class TestCSSHiddenFilter:
    """Test filter_css_hidden_pass."""

    def test_keeps_visible_element(self):
        """Test that visible elements are kept."""
        div = DomTreeNode(data=DomElement(tag="div", styles={"display": "block"}))

        result = filter_css_hidden_pass(div)

        assert result is not None
        assert isinstance(result.data, DomElement)

    def test_removes_display_none(self):
        """Test that elements with display:none are removed."""
        div = DomTreeNode(data=DomElement(tag="div", styles={"display": "none"}))

        result = filter_css_hidden_pass(div)

        assert result is None

    def test_removes_visibility_hidden(self):
        """Test that elements with visibility:hidden are removed."""
        div = DomTreeNode(data=DomElement(tag="div", styles={"visibility": "hidden"}))

        result = filter_css_hidden_pass(div)

        assert result is None

    def test_removes_opacity_zero(self):
        """Test that elements with opacity:0 are removed."""
        div = DomTreeNode(data=DomElement(tag="div", styles={"opacity": "0"}))

        result = filter_css_hidden_pass(div)

        assert result is None

    def test_keeps_opacity_non_zero(self):
        """Test that elements with opacity > 0 are kept."""
        div = DomTreeNode(data=DomElement(tag="div", styles={"opacity": "0.5"}))

        result = filter_css_hidden_pass(div)

        assert result is not None

    def test_inline_style_overrides_computed(self):
        """Test that inline styles override computed styles."""
        # Computed style says block, inline says none
        div = DomTreeNode(data=DomElement(
            tag="div",
            styles={"display": "block"},
            attributes={"style": "display: none"}
        ))

        result = filter_css_hidden_pass(div)

        assert result is None

    def test_removes_hidden_attribute(self):
        """Test that elements with hidden attribute are removed."""
        div = DomTreeNode(data=DomElement(tag="div", attributes={"hidden": ""}))

        result = filter_css_hidden_pass(div)

        assert result is None

    def test_removes_hidden_input(self):
        """Test that hidden input elements are removed."""
        input_elem = DomTreeNode(data=DomElement(
            tag="input",
            attributes={"type": "hidden"}
        ))

        result = filter_css_hidden_pass(input_elem)

        assert result is None

    def test_keeps_text_input(self):
        """Test that text input elements are kept."""
        input_elem = DomTreeNode(data=DomElement(
            tag="input",
            attributes={"type": "text"}
        ))

        result = filter_css_hidden_pass(input_elem)

        assert result is not None

    def test_keeps_text_nodes(self):
        """Test that text nodes are always kept."""
        text = DomTreeNode(data=DomText(text="Hello"))

        result = filter_css_hidden_pass(text)

        assert result is not None
        assert isinstance(result.data, DomText)

    def test_filters_children_recursively(self):
        """Test that children are filtered recursively."""
        div = DomTreeNode(data=DomElement(tag="div"))
        hidden_child = DomTreeNode(data=DomElement(tag="p", styles={"display": "none"}))
        visible_child = DomTreeNode(data=DomElement(tag="span"))

        div.add_child(hidden_child)
        div.add_child(visible_child)

        result = filter_css_hidden_pass(div)

        assert result is not None
        element_children = result.get_element_children()
        assert len(element_children) == 1
        assert element_children[0].data.tag == "span"

    def test_case_insensitive_css_values(self):
        """Test that CSS values are case-insensitive."""
        div = DomTreeNode(data=DomElement(tag="div", styles={"display": "NONE"}))

        result = filter_css_hidden_pass(div)

        assert result is None

    def test_invalid_opacity_value(self):
        """Test handling of invalid opacity value."""
        div = DomTreeNode(data=DomElement(tag="div", styles={"opacity": "invalid"}))

        result = filter_css_hidden_pass(div)

        # Should not crash, should keep element
        assert result is not None


class TestZeroDimensionsFilter:
    """Test filter_zero_dimensions_pass."""

    def test_keeps_element_with_dimensions(self):
        """Test that elements with dimensions are kept."""
        bbox = BoundingBox(x=0, y=0, width=100, height=50)
        div = DomTreeNode(data=DomElement(tag="div", bounds=bbox))

        result = filter_zero_dimensions_pass(div)

        assert result is not None

    def test_removes_zero_width_element(self):
        """Test that elements with zero width are removed."""
        bbox = BoundingBox(x=0, y=0, width=0, height=50)
        div = DomTreeNode(data=DomElement(tag="div", bounds=bbox))

        result = filter_zero_dimensions_pass(div)

        assert result is None

    def test_removes_zero_height_element(self):
        """Test that elements with zero height are removed."""
        bbox = BoundingBox(x=0, y=0, width=100, height=0)
        div = DomTreeNode(data=DomElement(tag="div", bounds=bbox))

        result = filter_zero_dimensions_pass(div)

        assert result is None

    def test_removes_negative_dimensions(self):
        """Test that elements with negative dimensions are removed."""
        bbox = BoundingBox(x=0, y=0, width=-10, height=-10)
        div = DomTreeNode(data=DomElement(tag="div", bounds=bbox))

        result = filter_zero_dimensions_pass(div)

        assert result is None

    def test_keeps_element_without_bounds(self):
        """Test that elements without bounds info are kept."""
        div = DomTreeNode(data=DomElement(tag="div", bounds=None))

        result = filter_zero_dimensions_pass(div)

        assert result is not None

    def test_keeps_zero_dimension_container_with_children(self):
        """Test that zero-dimension containers with children are kept."""
        # Parent has zero dimensions but child has real dimensions
        bbox_zero = BoundingBox(x=0, y=0, width=0, height=0)
        bbox_real = BoundingBox(x=100, y=100, width=50, height=50)

        parent = DomTreeNode(data=DomElement(tag="div", bounds=bbox_zero))
        child = DomTreeNode(data=DomElement(tag="div", bounds=bbox_real))

        parent.add_child(child)

        result = filter_zero_dimensions_pass(parent)

        # Parent should be kept because it has children
        assert result is not None
        assert len(result.children) == 1

    def test_removes_zero_dimension_leaf_element(self):
        """Test that zero-dimension elements without children are removed."""
        bbox = BoundingBox(x=0, y=0, width=0, height=0)
        div = DomTreeNode(data=DomElement(tag="div", bounds=bbox))

        result = filter_zero_dimensions_pass(div)

        assert result is None

    def test_keeps_text_nodes(self):
        """Test that text nodes are always kept."""
        text = DomTreeNode(data=DomText(text="Hello"))

        result = filter_zero_dimensions_pass(text)

        assert result is not None

    def test_filters_children_recursively(self):
        """Test that children are filtered recursively."""
        bbox_good = BoundingBox(x=0, y=0, width=100, height=100)
        bbox_zero = BoundingBox(x=0, y=0, width=0, height=0)

        div = DomTreeNode(data=DomElement(tag="div", bounds=bbox_good))
        zero_child = DomTreeNode(data=DomElement(tag="p", bounds=bbox_zero))
        good_child = DomTreeNode(data=DomElement(tag="span", bounds=bbox_good))

        div.add_child(zero_child)
        div.add_child(good_child)

        result = filter_zero_dimensions_pass(div)

        assert result is not None
        element_children = result.get_element_children()
        # Zero-dimension child without children should be filtered
        assert len(element_children) == 1
        assert element_children[0].data.tag == "span"

    def test_nested_zero_dimension_container(self):
        """Test nested zero-dimension containers."""
        bbox_zero = BoundingBox(x=0, y=0, width=0, height=0)
        bbox_good = BoundingBox(x=0, y=0, width=100, height=100)

        # grandparent (zero) > parent (zero) > child (good)
        grandparent = DomTreeNode(data=DomElement(tag="div", bounds=bbox_zero))
        parent = DomTreeNode(data=DomElement(tag="div", bounds=bbox_zero))
        child = DomTreeNode(data=DomElement(tag="div", bounds=bbox_good))

        grandparent.add_child(parent)
        parent.add_child(child)

        result = filter_zero_dimensions_pass(grandparent)

        # All should be kept because they form a chain to a visible element
        assert result is not None
        assert len(result.children) == 1
        assert len(result.children[0].children) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
