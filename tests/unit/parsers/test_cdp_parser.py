"""Unit tests for CDP parser."""

import pytest
from domcontext._internal.parsers.cdp_parser import parse_cdp_snapshot
from domcontext._internal.ir.dom_ir import DomElement, DomText, DomIR, BoundingBox


class TestCDPParser:
    """Test CDP parser functionality."""

    def test_parse_simple_element(self):
        """Test parsing a simple element."""
        snapshot = {
            'documents': [{
                'nodes': {
                    'nodeType': [1],  # Element
                    'nodeName': [0],  # Index to "div"
                    'nodeValue': [-1],
                    'parentIndex': [-1],  # Root
                    'attributes': [[]]
                }
            }],
            'strings': ['div']
        }

        dom_ir = parse_cdp_snapshot(snapshot)

        assert isinstance(dom_ir, DomIR)
        assert dom_ir.root is not None
        assert isinstance(dom_ir.root.data, DomElement)
        assert dom_ir.root.data.tag == 'div'
        assert dom_ir.root.data.cdp_index == 0

    def test_parse_element_with_attributes(self):
        """Test parsing element with attributes."""
        snapshot = {
            'documents': [{
                'nodes': {
                    'nodeType': [1],
                    'nodeName': [0],  # 'input'
                    'nodeValue': [-1],
                    'parentIndex': [-1],
                    'attributes': [[1, 2, 3, 4]]  # type="text", name="username"
                }
            }],
            'strings': ['input', 'type', 'text', 'name', 'username']
        }

        dom_ir = parse_cdp_snapshot(snapshot)

        input_node = dom_ir.root
        assert input_node.data.tag == 'input'
        assert input_node.data.attributes['type'] == 'text'
        assert input_node.data.attributes['name'] == 'username'

    def test_parse_with_text_node(self):
        """Test parsing element with text content."""
        snapshot = {
            'documents': [{
                'nodes': {
                    'nodeType': [1, 3],  # Element, Text
                    'nodeName': [0, -1],  # 'p', n/a for text
                    'nodeValue': [-1, 1],  # n/a, 'Hello World'
                    'parentIndex': [-1, 0],  # root, child of p
                    'attributes': [[], []]
                }
            }],
            'strings': ['p', 'Hello World']
        }

        dom_ir = parse_cdp_snapshot(snapshot)

        p_node = dom_ir.root
        assert p_node.data.tag == 'p'

        # Check text children
        text_children = p_node.get_text_children()
        assert len(text_children) == 1
        assert isinstance(text_children[0].data, DomText)
        assert text_children[0].data.text == 'Hello World'

    def test_parse_nested_structure(self):
        """Test parsing nested element structure."""
        snapshot = {
            'documents': [{
                'nodes': {
                    'nodeType': [1, 1, 1],  # div, section, p
                    'nodeName': [0, 1, 2],
                    'nodeValue': [-1, -1, -1],
                    'parentIndex': [-1, 0, 1],  # div is root, section child of div, p child of section
                    'attributes': [[], [], []]
                }
            }],
            'strings': ['div', 'section', 'p']
        }

        dom_ir = parse_cdp_snapshot(snapshot)

        div_node = dom_ir.root
        assert div_node.data.tag == 'div'

        section_children = div_node.get_element_children()
        assert len(section_children) == 1
        assert section_children[0].data.tag == 'section'

        p_children = section_children[0].get_element_children()
        assert len(p_children) == 1
        assert p_children[0].data.tag == 'p'

    def test_parse_with_layout_bounds(self):
        """Test parsing element with bounding box."""
        snapshot = {
            'documents': [{
                'nodes': {
                    'nodeType': [1],
                    'nodeName': [0],
                    'nodeValue': [-1],
                    'parentIndex': [-1],
                    'attributes': [[]]
                },
                'layout': {
                    'nodeIndex': [0],
                    'bounds': [[10, 20, 100, 50]],  # x, y, width, height
                    'styles': [[]]
                }
            }],
            'strings': ['button']
        }

        dom_ir = parse_cdp_snapshot(snapshot)

        button_node = dom_ir.root
        assert button_node.data.tag == 'button'
        assert button_node.data.bounds is not None
        assert button_node.data.bounds.x == 10
        assert button_node.data.bounds.y == 20
        assert button_node.data.bounds.width == 100
        assert button_node.data.bounds.height == 50

    def test_parse_with_layout_styles(self):
        """Test parsing element with computed styles."""
        snapshot = {
            'documents': [{
                'nodes': {
                    'nodeType': [1],
                    'nodeName': [0],
                    'nodeValue': [-1],
                    'parentIndex': [-1],
                    'attributes': [[]]
                },
                'layout': {
                    'nodeIndex': [0],
                    'bounds': [[0, 0, 0, 0]],
                    'styles': [[1, 2, 3, 4]]  # display: none, visibility: hidden
                }
            }],
            'strings': ['div', 'display', 'none', 'visibility', 'hidden']
        }

        dom_ir = parse_cdp_snapshot(snapshot)

        div_node = dom_ir.root
        assert div_node.data.styles['display'] == 'none'
        assert div_node.data.styles['visibility'] == 'hidden'

    def test_parse_empty_snapshot(self):
        """Test parsing empty CDP snapshot."""
        snapshot = {
            'documents': [],
            'strings': []
        }

        dom_ir = parse_cdp_snapshot(snapshot)

        assert isinstance(dom_ir, DomIR)
        assert dom_ir.root is not None
        assert dom_ir.root.data.tag == 'html'

    def test_parse_missing_optional_fields(self):
        """Test parsing with missing optional layout data."""
        snapshot = {
            'documents': [{
                'nodes': {
                    'nodeType': [1],
                    'nodeName': [0],
                    'nodeValue': [-1],
                    'parentIndex': [-1],
                    'attributes': [[]]
                }
                # No layout data
            }],
            'strings': ['div']
        }

        dom_ir = parse_cdp_snapshot(snapshot)

        div_node = dom_ir.root
        assert div_node.data.tag == 'div'
        assert div_node.data.bounds is None
        assert div_node.data.styles == {}

    def test_parse_multiple_siblings(self):
        """Test parsing multiple sibling elements."""
        snapshot = {
            'documents': [{
                'nodes': {
                    'nodeType': [1, 1, 1, 1],  # ul, li, li, li
                    'nodeName': [0, 1, 1, 1],
                    'nodeValue': [-1, -1, -1, -1],
                    'parentIndex': [-1, 0, 0, 0],  # ul is root, all li's are children of ul
                    'attributes': [[], [], [], []]
                }
            }],
            'strings': ['ul', 'li']
        }

        dom_ir = parse_cdp_snapshot(snapshot)

        ul_node = dom_ir.root
        assert ul_node.data.tag == 'ul'

        li_children = ul_node.get_element_children()
        assert len(li_children) == 3
        assert all(child.data.tag == 'li' for child in li_children)

    def test_parent_child_relationships(self):
        """Test that parent-child relationships are correctly established."""
        snapshot = {
            'documents': [{
                'nodes': {
                    'nodeType': [1, 1],  # div, p
                    'nodeName': [0, 1],
                    'nodeValue': [-1, -1],
                    'parentIndex': [-1, 0],
                    'attributes': [[], []]
                }
            }],
            'strings': ['div', 'p']
        }

        dom_ir = parse_cdp_snapshot(snapshot)

        div_node = dom_ir.root
        p_children = div_node.get_element_children()

        assert len(p_children) == 1
        p_node = p_children[0]

        # Verify parent reference
        assert p_node.parent is div_node
        assert p_node.data.tag == 'p'

    def test_parse_complex_tree(self):
        """Test parsing a complex tree with mixed content."""
        snapshot = {
            'documents': [{
                'nodes': {
                    # 0: html, 1: body, 2: div, 3: text, 4: p, 5: text
                    'nodeType': [1, 1, 1, 3, 1, 3],
                    'nodeName': [0, 1, 2, -1, 3, -1],
                    'nodeValue': [-1, -1, -1, 4, -1, 5],
                    'parentIndex': [-1, 0, 1, 2, 2, 4],
                    'attributes': [[], [], [], [], [], []]
                }
            }],
            'strings': ['html', 'body', 'div', 'p', 'Hello', 'World']
        }

        dom_ir = parse_cdp_snapshot(snapshot)

        html_node = dom_ir.root
        assert html_node.data.tag == 'html'

        body_children = html_node.get_element_children()
        assert len(body_children) == 1
        assert body_children[0].data.tag == 'body'

        div_children = body_children[0].get_element_children()
        assert len(div_children) == 1
        assert div_children[0].data.tag == 'div'

        # Check div has both text and p element
        div_node = div_children[0]
        all_text = div_node.get_all_text()
        assert 'Hello' in all_text
        assert 'World' in all_text

    def test_cdp_index_preserved(self):
        """Test that CDP node indices are preserved."""
        snapshot = {
            'documents': [{
                'nodes': {
                    'nodeType': [1, 1, 1],
                    'nodeName': [0, 0, 0],
                    'nodeValue': [-1, -1, -1],
                    'parentIndex': [-1, 0, 0],
                    'attributes': [[], [], []]
                }
            }],
            'strings': ['div']
        }

        dom_ir = parse_cdp_snapshot(snapshot)

        all_elements = dom_ir.all_element_nodes()

        # Check that CDP indices match their position in the arrays
        assert all_elements[0].data.cdp_index == 0
        assert all_elements[1].data.cdp_index == 1
        assert all_elements[2].data.cdp_index == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
