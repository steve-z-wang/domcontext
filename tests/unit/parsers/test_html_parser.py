"""Unit tests for HTML parser."""

import pytest

from domcontext._internal.ir.dom_ir import DomElement, DomIR, DomText
from domcontext._internal.parsers.html_parser import parse_html


class TestHTMLParser:
    """Test HTML parser functionality."""

    def test_parse_simple_html(self):
        """Test parsing simple valid HTML."""
        html = "<html><body><p>Hello</p></body></html>"
        dom_ir = parse_html(html)

        assert isinstance(dom_ir, DomIR)
        assert dom_ir.root is not None
        assert isinstance(dom_ir.root.data, DomElement)
        assert dom_ir.root.data.tag == "html"

    def test_parse_with_text_content(self):
        """Test parsing HTML with text content."""
        html = "<p>Hello World</p>"
        dom_ir = parse_html(html)

        # Get p element
        p_node = dom_ir.root
        assert p_node.data.tag == "p"

        # Check text children
        text_children = p_node.get_text_children()
        assert len(text_children) > 0
        assert isinstance(text_children[0].data, DomText)
        assert "Hello World" in text_children[0].data.text

    def test_parse_nested_structure(self):
        """Test parsing nested HTML structure."""
        html = """
        <div>
            <section>
                <p>Nested</p>
            </section>
        </div>
        """
        dom_ir = parse_html(html)

        # Verify nesting
        div_node = dom_ir.root
        assert div_node.data.tag == "div"

        section_children = div_node.get_element_children()
        assert len(section_children) > 0
        assert section_children[0].data.tag == "section"

        p_children = section_children[0].get_element_children()
        assert len(p_children) > 0
        assert p_children[0].data.tag == "p"

    def test_parse_with_attributes(self):
        """Test parsing HTML with attributes."""
        html = '<input type="text" placeholder="Enter name" name="username"/>'
        dom_ir = parse_html(html)

        input_node = dom_ir.root
        assert input_node.data.tag == "input"
        assert input_node.data.attributes["type"] == "text"
        assert input_node.data.attributes["placeholder"] == "Enter name"
        assert input_node.data.attributes["name"] == "username"

    def test_parse_with_backend_node_id(self):
        """Test parsing HTML with backend_node_id attribute."""
        html = '<button backend_node_id="123">Click</button>'
        dom_ir = parse_html(html)

        button_node = dom_ir.root
        assert button_node.data.tag == "button"
        assert button_node.data.attributes.get("backend_node_id") == "123"

    def test_parse_empty_html(self):
        """Test parsing empty HTML."""
        html = ""
        dom_ir = parse_html(html)

        assert isinstance(dom_ir, DomIR)
        assert dom_ir.root is not None

    def test_parse_malformed_html(self):
        """Test parsing malformed HTML (should recover)."""
        html = "<div><p>Unclosed paragraph<div>Another div</div>"
        dom_ir = parse_html(html)

        # lxml should recover and parse
        assert isinstance(dom_ir, DomIR)
        assert dom_ir.root is not None

    def test_parse_special_characters(self):
        """Test parsing HTML with special characters."""
        html = '<p>Special: &lt;&gt;&amp;"</p>'
        dom_ir = parse_html(html)

        p_node = dom_ir.root
        text_content = p_node.get_all_text()
        # lxml should decode entities
        assert "<" in text_content or "&lt;" in text_content

    def test_parent_child_relationships(self):
        """Test that parent-child relationships are correctly established."""
        html = "<div><p>Child</p></div>"
        dom_ir = parse_html(html)

        div_node = dom_ir.root
        p_children = div_node.get_element_children()

        assert len(p_children) == 1
        p_node = p_children[0]

        # Verify parent reference
        assert p_node.parent is div_node
        assert p_node.data.tag == "p"

    def test_multiple_children(self):
        """Test parsing element with multiple children."""
        html = """
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
            <li>Item 3</li>
        </ul>
        """
        dom_ir = parse_html(html)

        ul_node = dom_ir.root
        li_children = ul_node.get_element_children()

        assert len(li_children) == 3
        assert all(child.data.tag == "li" for child in li_children)

    def test_walk_up_tree(self):
        """Test walking up the tree to root."""
        html = "<html><body><div><p>Deep</p></div></body></html>"
        dom_ir = parse_html(html)

        # Find the p element
        html_node = dom_ir.root
        body_node = html_node.get_element_children()[0]
        div_node = body_node.get_element_children()[0]
        p_node = div_node.get_element_children()[0]

        # Walk up from p to root
        path = p_node.walk_up()

        assert len(path) == 4  # p, div, body, html
        assert path[0] is p_node
        assert path[-1] is html_node

    def test_get_all_text(self):
        """Test extracting all text from element tree."""
        html = """
        <div>
            <p>First paragraph</p>
            <p>Second paragraph</p>
        </div>
        """
        dom_ir = parse_html(html)

        div_node = dom_ir.root
        all_text = div_node.get_all_text()

        assert "First paragraph" in all_text
        assert "Second paragraph" in all_text

    def test_dom_ir_indexing(self):
        """Test DomIR element indexing."""
        html = "<div><p>Text</p><span>More</span></div>"
        dom_ir = parse_html(html)

        # Get all element nodes
        all_elements = dom_ir.all_element_nodes()

        assert len(all_elements) >= 3  # div, p, span
        tags = [node.data.tag for node in all_elements]
        assert "div" in tags
        assert "p" in tags
        assert "span" in tags


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
