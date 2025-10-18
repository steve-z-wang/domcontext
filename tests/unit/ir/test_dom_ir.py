"""Unit tests for DomIR."""

import pytest
from domcontext._internal.ir.dom_ir import (
    BoundingBox,
    DomElement,
    DomText,
    DomTreeNode,
    DomIR
)


class TestBoundingBox:
    """Test BoundingBox dataclass."""

    def test_create_bounding_box(self):
        """Test creating a bounding box."""
        bbox = BoundingBox(x=10.5, y=20.0, width=100.0, height=50.5)

        assert bbox.x == 10.5
        assert bbox.y == 20.0
        assert bbox.width == 100.0
        assert bbox.height == 50.5


class TestDomElement:
    """Test DomElement class."""

    def test_create_minimal_element(self):
        """Test creating element with only tag."""
        elem = DomElement(tag="div")

        assert elem.tag == "div"
        assert elem.cdp_index is None
        assert elem.attributes == {}
        assert elem.styles == {}
        assert elem.bounds is None

    def test_create_full_element(self):
        """Test creating element with all fields."""
        bbox = BoundingBox(x=0, y=0, width=100, height=50)
        elem = DomElement(
            tag="button",
            cdp_index=42,
            attributes={"type": "submit", "name": "btn"},
            styles={"display": "block", "color": "red"},
            bounds=bbox
        )

        assert elem.tag == "button"
        assert elem.cdp_index == 42
        assert elem.attributes["type"] == "submit"
        assert elem.attributes["name"] == "btn"
        assert elem.styles["display"] == "block"
        assert elem.styles["color"] == "red"
        assert elem.bounds is bbox
        assert elem.bounds.width == 100

    def test_element_repr(self):
        """Test element string representation."""
        elem = DomElement(tag="input", attributes={"type": "text", "name": "user"})

        repr_str = repr(elem)
        assert "DomElement" in repr_str
        assert "input" in repr_str
        assert "2" in repr_str  # 2 attributes


class TestDomText:
    """Test DomText class."""

    def test_create_text(self):
        """Test creating text node."""
        text = DomText(text="Hello World")

        assert text.text == "Hello World"

    def test_text_repr_short(self):
        """Test text repr with short text."""
        text = DomText(text="Short text")

        repr_str = repr(text)
        assert "DomText" in repr_str
        assert "Short text" in repr_str

    def test_text_repr_long(self):
        """Test text repr with long text (should be truncated)."""
        long_text = "A" * 100
        text = DomText(text=long_text)

        repr_str = repr(text)
        assert "DomText" in repr_str
        assert "..." in repr_str  # Should be truncated


class TestDomTreeNode:
    """Test DomTreeNode class."""

    def test_create_node_with_element(self):
        """Test creating node with element data."""
        elem = DomElement(tag="div")
        node = DomTreeNode(data=elem)

        assert node.data is elem
        assert node.parent is None
        assert len(node.children) == 0

    def test_create_node_with_text(self):
        """Test creating node with text data."""
        text = DomText(text="Hello")
        node = DomTreeNode(data=text)

        assert node.data is text
        assert node.parent is None
        assert len(node.children) == 0

    def test_add_child(self):
        """Test adding child nodes."""
        parent = DomTreeNode(data=DomElement(tag="div"))
        child1 = DomTreeNode(data=DomElement(tag="p"))
        child2 = DomTreeNode(data=DomText(text="Hello"))

        parent.add_child(child1)
        parent.add_child(child2)

        assert len(parent.children) == 2
        assert parent.children[0] is child1
        assert parent.children[1] is child2
        assert child1.parent is parent
        assert child2.parent is parent

    def test_get_element_children(self):
        """Test getting only element children."""
        parent = DomTreeNode(data=DomElement(tag="div"))
        elem_child1 = DomTreeNode(data=DomElement(tag="p"))
        text_child = DomTreeNode(data=DomText(text="Text"))
        elem_child2 = DomTreeNode(data=DomElement(tag="span"))

        parent.add_child(elem_child1)
        parent.add_child(text_child)
        parent.add_child(elem_child2)

        element_children = parent.get_element_children()

        assert len(element_children) == 2
        assert elem_child1 in element_children
        assert elem_child2 in element_children
        assert text_child not in element_children

    def test_get_text_children(self):
        """Test getting only text children."""
        parent = DomTreeNode(data=DomElement(tag="div"))
        elem_child = DomTreeNode(data=DomElement(tag="p"))
        text_child1 = DomTreeNode(data=DomText(text="Hello"))
        text_child2 = DomTreeNode(data=DomText(text="World"))

        parent.add_child(elem_child)
        parent.add_child(text_child1)
        parent.add_child(text_child2)

        text_children = parent.get_text_children()

        assert len(text_children) == 2
        assert text_child1 in text_children
        assert text_child2 in text_children
        assert elem_child not in text_children

    def test_get_all_text_simple(self):
        """Test getting all text from simple structure."""
        parent = DomTreeNode(data=DomElement(tag="p"))
        text_child = DomTreeNode(data=DomText(text="Hello World"))

        parent.add_child(text_child)

        all_text = parent.get_all_text()
        assert all_text == "Hello World"

    def test_get_all_text_multiple(self):
        """Test getting all text from multiple text nodes."""
        parent = DomTreeNode(data=DomElement(tag="p"))
        text1 = DomTreeNode(data=DomText(text="Hello"))
        text2 = DomTreeNode(data=DomText(text="World"))

        parent.add_child(text1)
        parent.add_child(text2)

        all_text = parent.get_all_text()
        assert "Hello" in all_text
        assert "World" in all_text

    def test_get_all_text_nested(self):
        """Test getting all text from nested structure."""
        div = DomTreeNode(data=DomElement(tag="div"))
        p = DomTreeNode(data=DomElement(tag="p"))
        text1 = DomTreeNode(data=DomText(text="First"))
        text2 = DomTreeNode(data=DomText(text="Second"))

        div.add_child(text1)
        div.add_child(p)
        p.add_child(text2)

        all_text = div.get_all_text()
        assert "First" in all_text
        assert "Second" in all_text

    def test_walk_up_single_node(self):
        """Test walking up from single node."""
        node = DomTreeNode(data=DomElement(tag="div"))

        path = node.walk_up()

        assert len(path) == 1
        assert path[0] is node

    def test_walk_up_nested(self):
        """Test walking up from deeply nested node."""
        root = DomTreeNode(data=DomElement(tag="html"))
        body = DomTreeNode(data=DomElement(tag="body"))
        div = DomTreeNode(data=DomElement(tag="div"))
        p = DomTreeNode(data=DomElement(tag="p"))

        root.add_child(body)
        body.add_child(div)
        div.add_child(p)

        path = p.walk_up()

        assert len(path) == 4
        assert path[0] is p
        assert path[1] is div
        assert path[2] is body
        assert path[3] is root

    def test_node_repr(self):
        """Test node string representation."""
        elem = DomElement(tag="div")
        node = DomTreeNode(data=elem)
        child = DomTreeNode(data=DomElement(tag="p"))
        node.add_child(child)

        repr_str = repr(node)
        assert "DomTreeNode" in repr_str
        assert "DomElement" in repr_str
        assert "1" in repr_str  # 1 child


class TestDomIR:
    """Test DomIR class."""

    def test_create_dom_ir(self):
        """Test creating DomIR with root node."""
        root = DomTreeNode(data=DomElement(tag="html"))
        dom_ir = DomIR(root=root)

        assert dom_ir.root is root
        assert dom_ir._element_index is None  # Lazy initialization

    def test_build_index(self):
        """Test building element index."""
        root = DomTreeNode(data=DomElement(tag="html"))
        body = DomTreeNode(data=DomElement(tag="body"))
        div = DomTreeNode(data=DomElement(tag="div"))

        root.add_child(body)
        body.add_child(div)

        dom_ir = DomIR(root=root)
        dom_ir._build_index()

        assert dom_ir._element_index is not None
        assert len(dom_ir._element_index) == 3
        assert root.data in dom_ir._element_index
        assert body.data in dom_ir._element_index
        assert div.data in dom_ir._element_index

    def test_get_node_by_element(self):
        """Test getting node by element."""
        elem = DomElement(tag="button")
        node = DomTreeNode(data=elem)
        root = DomTreeNode(data=DomElement(tag="div"))
        root.add_child(node)

        dom_ir = DomIR(root=root)
        found_node = dom_ir.get_node_by_element(elem)

        assert found_node is node

    def test_get_node_by_element_not_found(self):
        """Test getting node by element that doesn't exist."""
        root = DomTreeNode(data=DomElement(tag="div"))
        dom_ir = DomIR(root=root)

        other_elem = DomElement(tag="span")
        found_node = dom_ir.get_node_by_element(other_elem)

        assert found_node is None

    def test_all_element_nodes(self):
        """Test getting all element nodes."""
        root = DomTreeNode(data=DomElement(tag="html"))
        body = DomTreeNode(data=DomElement(tag="body"))
        div = DomTreeNode(data=DomElement(tag="div"))
        text = DomTreeNode(data=DomText(text="Hello"))

        root.add_child(body)
        body.add_child(div)
        div.add_child(text)

        dom_ir = DomIR(root=root)
        all_elements = dom_ir.all_element_nodes()

        # Should only get elements, not text
        assert len(all_elements) == 3
        assert root in all_elements
        assert body in all_elements
        assert div in all_elements

    def test_to_dict_simple(self):
        """Test serializing simple tree to dict."""
        elem = DomElement(tag="div", attributes={"class": "test"})
        root = DomTreeNode(data=elem)

        dom_ir = DomIR(root=root)
        result = dom_ir.to_dict()

        assert result['total_nodes'] == 1
        assert result['root']['type'] == 'element'
        assert result['root']['tag'] == 'div'
        assert result['root']['attributes'] == {"class": "test"}
        assert result['root']['styles'] == {}
        assert result['root']['bounds'] is None
        assert result['root']['children'] == []

    def test_to_dict_with_children(self):
        """Test serializing tree with children to dict."""
        root = DomTreeNode(data=DomElement(tag="div"))
        text = DomTreeNode(data=DomText(text="Hello"))
        p = DomTreeNode(data=DomElement(tag="p"))

        root.add_child(text)
        root.add_child(p)

        dom_ir = DomIR(root=root)
        result = dom_ir.to_dict()

        assert result['total_nodes'] == 2  # div and p (not text)
        assert len(result['root']['children']) == 2
        assert result['root']['children'][0]['type'] == 'text'
        assert result['root']['children'][0]['text'] == 'Hello'
        assert result['root']['children'][1]['type'] == 'element'
        assert result['root']['children'][1]['tag'] == 'p'

    def test_to_dict_with_bounds(self):
        """Test serializing tree with bounds to dict."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50)
        elem = DomElement(tag="button", bounds=bbox)
        root = DomTreeNode(data=elem)

        dom_ir = DomIR(root=root)
        result = dom_ir.to_dict()

        assert result['root']['bounds'] is not None
        assert result['root']['bounds']['x'] == 10
        assert result['root']['bounds']['y'] == 20
        assert result['root']['bounds']['width'] == 100
        assert result['root']['bounds']['height'] == 50

    def test_dom_ir_repr(self):
        """Test DomIR string representation."""
        root = DomTreeNode(data=DomElement(tag="html"))
        body = DomTreeNode(data=DomElement(tag="body"))
        root.add_child(body)

        dom_ir = DomIR(root=root)
        repr_str = repr(dom_ir)

        assert "DomIR" in repr_str
        assert "html" in repr_str
        assert "2" in repr_str  # 2 nodes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
