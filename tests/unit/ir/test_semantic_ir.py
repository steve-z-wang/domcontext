"""Unit tests for SemanticIR."""

import pytest
from domcontext._internal.ir.semantic_ir import (
    SemanticElement,
    SemanticText,
    SemanticTreeNode,
    SemanticIR
)


class TestSemanticElement:
    """Test SemanticElement class."""

    def test_create_minimal_element(self):
        """Test creating element with only tag."""
        elem = SemanticElement(tag="div")

        assert elem.tag == "div"
        assert elem.semantic_attributes == {}
        assert elem.dom_tree_node is None
        assert elem.readable_id is None

    def test_create_full_element(self):
        """Test creating element with all fields."""
        elem = SemanticElement(
            tag="button",
            semantic_attributes={"type": "submit", "name": "btn"},
            readable_id="button-1"
        )

        assert elem.tag == "button"
        assert elem.semantic_attributes["type"] == "submit"
        assert elem.semantic_attributes["name"] == "btn"
        assert elem.readable_id == "button-1"

    def test_to_markdown_simple(self):
        """Test markdown serialization with just tag."""
        elem = SemanticElement(tag="div")

        markdown = elem.to_markdown()
        assert markdown == "div"

    def test_to_markdown_with_id(self):
        """Test markdown serialization with readable ID."""
        elem = SemanticElement(tag="button", readable_id="button-1")

        markdown = elem.to_markdown()
        assert markdown == "button-1"

    def test_to_markdown_with_attributes(self):
        """Test markdown serialization with attributes."""
        elem = SemanticElement(
            tag="input",
            semantic_attributes={"type": "text", "name": "username"}
        )

        markdown = elem.to_markdown()
        assert 'type="text"' in markdown
        assert 'name="username"' in markdown

    def test_to_markdown_with_id_and_attributes(self):
        """Test markdown serialization with both ID and attributes."""
        elem = SemanticElement(
            tag="button",
            readable_id="button-1",
            semantic_attributes={"type": "submit"}
        )

        markdown = elem.to_markdown()
        assert "button-1" in markdown
        assert 'type="submit"' in markdown

    def test_element_repr(self):
        """Test element string representation."""
        elem = SemanticElement(
            tag="input",
            semantic_attributes={"type": "text"},
            readable_id="input-1"
        )

        repr_str = repr(elem)
        assert "SemanticElement" in repr_str
        assert "input" in repr_str
        assert "input-1" in repr_str


class TestSemanticText:
    """Test SemanticText class."""

    def test_create_text(self):
        """Test creating text node."""
        text = SemanticText(text="Hello World")

        assert text.text == "Hello World"
        assert text.dom_tree_node is None

    def test_to_markdown(self):
        """Test markdown serialization."""
        text = SemanticText(text="Click here")

        markdown = text.to_markdown()
        assert markdown == '"Click here"'

    def test_text_repr_short(self):
        """Test text repr with short text."""
        text = SemanticText(text="Short")

        repr_str = repr(text)
        assert "SemanticText" in repr_str
        assert "Short" in repr_str

    def test_text_repr_long(self):
        """Test text repr with long text (should be truncated)."""
        long_text = "A" * 100
        text = SemanticText(text=long_text)

        repr_str = repr(text)
        assert "SemanticText" in repr_str
        assert "..." in repr_str


class TestSemanticTreeNode:
    """Test SemanticTreeNode class."""

    def test_create_node_with_element(self):
        """Test creating node with element data."""
        elem = SemanticElement(tag="div")
        node = SemanticTreeNode(data=elem)

        assert node.data is elem
        assert len(node.children) == 0

    def test_create_node_with_text(self):
        """Test creating node with text data."""
        text = SemanticText(text="Hello")
        node = SemanticTreeNode(data=text)

        assert node.data is text
        assert len(node.children) == 0

    def test_add_child(self):
        """Test adding child nodes (no parent reference)."""
        parent = SemanticTreeNode(data=SemanticElement(tag="div"))
        child1 = SemanticTreeNode(data=SemanticElement(tag="p"))
        child2 = SemanticTreeNode(data=SemanticText(text="Hello"))

        parent.add_child(child1)
        parent.add_child(child2)

        assert len(parent.children) == 2
        assert parent.children[0] is child1
        assert parent.children[1] is child2
        # No parent reference in SemanticTreeNode
        assert not hasattr(child1, 'parent')

    def test_get_element_children(self):
        """Test getting only element children."""
        parent = SemanticTreeNode(data=SemanticElement(tag="div"))
        elem_child1 = SemanticTreeNode(data=SemanticElement(tag="p"))
        text_child = SemanticTreeNode(data=SemanticText(text="Text"))
        elem_child2 = SemanticTreeNode(data=SemanticElement(tag="span"))

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
        parent = SemanticTreeNode(data=SemanticElement(tag="div"))
        elem_child = SemanticTreeNode(data=SemanticElement(tag="p"))
        text_child1 = SemanticTreeNode(data=SemanticText(text="Hello"))
        text_child2 = SemanticTreeNode(data=SemanticText(text="World"))

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
        parent = SemanticTreeNode(data=SemanticElement(tag="p"))
        text_child = SemanticTreeNode(data=SemanticText(text="Hello World"))

        parent.add_child(text_child)

        all_text = parent.get_all_text()
        assert all_text == "Hello World"

    def test_get_all_text_nested(self):
        """Test getting all text from nested structure."""
        div = SemanticTreeNode(data=SemanticElement(tag="div"))
        p = SemanticTreeNode(data=SemanticElement(tag="p"))
        text1 = SemanticTreeNode(data=SemanticText(text="First"))
        text2 = SemanticTreeNode(data=SemanticText(text="Second"))

        div.add_child(text1)
        div.add_child(p)
        p.add_child(text2)

        all_text = div.get_all_text()
        assert "First" in all_text
        assert "Second" in all_text

    def test_node_repr(self):
        """Test node string representation."""
        elem = SemanticElement(tag="div")
        node = SemanticTreeNode(data=elem)
        child = SemanticTreeNode(data=SemanticElement(tag="p"))
        node.add_child(child)

        repr_str = repr(node)
        assert "SemanticTreeNode" in repr_str
        assert "SemanticElement" in repr_str
        assert "1" in repr_str  # 1 child


class TestSemanticIR:
    """Test SemanticIR class."""

    def test_create_semantic_ir(self):
        """Test creating SemanticIR with root node."""
        root = SemanticTreeNode(data=SemanticElement(tag="body"))
        semantic_ir = SemanticIR(root=root)

        assert semantic_ir.root is root
        assert semantic_ir._element_index is None  # Lazy initialization

    def test_create_with_id_index(self):
        """Test creating SemanticIR with pre-built ID index."""
        elem = SemanticElement(tag="button", readable_id="button-1")
        root = SemanticTreeNode(data=elem)
        id_index = {"button-1": elem}

        semantic_ir = SemanticIR(root=root, id_index=id_index)

        assert semantic_ir._id_index is id_index

    def test_build_index(self):
        """Test building element index."""
        root = SemanticTreeNode(data=SemanticElement(tag="body"))
        div = SemanticTreeNode(data=SemanticElement(tag="div"))
        p = SemanticTreeNode(data=SemanticElement(tag="p"))

        root.add_child(div)
        div.add_child(p)

        semantic_ir = SemanticIR(root=root)
        semantic_ir._build_index()

        assert semantic_ir._element_index is not None
        assert len(semantic_ir._element_index) == 3
        assert root.data in semantic_ir._element_index
        assert div.data in semantic_ir._element_index
        assert p.data in semantic_ir._element_index

    def test_get_node_by_element(self):
        """Test getting node by element."""
        elem = SemanticElement(tag="button")
        node = SemanticTreeNode(data=elem)
        root = SemanticTreeNode(data=SemanticElement(tag="div"))
        root.add_child(node)

        semantic_ir = SemanticIR(root=root)
        found_node = semantic_ir.get_node_by_element(elem)

        assert found_node is node

    def test_get_element_by_id(self):
        """Test getting element by readable ID."""
        elem1 = SemanticElement(tag="button", readable_id="button-1")
        elem2 = SemanticElement(tag="input", readable_id="input-1")
        id_index = {"button-1": elem1, "input-1": elem2}

        root = SemanticTreeNode(data=elem1)
        semantic_ir = SemanticIR(root=root, id_index=id_index)

        found = semantic_ir.get_element_by_id("button-1")
        assert found is elem1

    def test_get_element_by_id_not_found(self):
        """Test getting element by ID that doesn't exist."""
        elem = SemanticElement(tag="button", readable_id="button-1")
        id_index = {"button-1": elem}

        root = SemanticTreeNode(data=elem)
        semantic_ir = SemanticIR(root=root, id_index=id_index)

        found = semantic_ir.get_element_by_id("button-99")
        assert found is None

    def test_get_all_elements_with_ids(self):
        """Test getting all elements with IDs."""
        elem1 = SemanticElement(tag="button", readable_id="button-1")
        elem2 = SemanticElement(tag="input", readable_id="input-1")
        id_index = {"button-1": elem1, "input-1": elem2}

        root = SemanticTreeNode(data=elem1)
        semantic_ir = SemanticIR(root=root, id_index=id_index)

        all_with_ids = semantic_ir.get_all_elements_with_ids()

        assert len(all_with_ids) == 2
        assert all_with_ids["button-1"] is elem1
        assert all_with_ids["input-1"] is elem2

    def test_all_element_nodes(self):
        """Test getting all element nodes."""
        root = SemanticTreeNode(data=SemanticElement(tag="body"))
        div = SemanticTreeNode(data=SemanticElement(tag="div"))
        text = SemanticTreeNode(data=SemanticText(text="Hello"))

        root.add_child(div)
        div.add_child(text)

        semantic_ir = SemanticIR(root=root)
        all_elements = semantic_ir.all_element_nodes()

        # Should only get elements, not text
        assert len(all_elements) == 2
        assert root in all_elements
        assert div in all_elements

    def test_dfs_simple(self):
        """Test DFS traversal without options."""
        root = SemanticTreeNode(data=SemanticElement(tag="body"))
        div = SemanticTreeNode(data=SemanticElement(tag="div"))
        p = SemanticTreeNode(data=SemanticElement(tag="p"))

        root.add_child(div)
        div.add_child(p)

        semantic_ir = SemanticIR(root=root)
        nodes = list(semantic_ir.dfs())

        assert len(nodes) == 3
        assert nodes[0] is root
        assert nodes[1] is div
        assert nodes[2] is p

    def test_dfs_with_depth(self):
        """Test DFS traversal with depth."""
        root = SemanticTreeNode(data=SemanticElement(tag="body"))
        div = SemanticTreeNode(data=SemanticElement(tag="div"))

        root.add_child(div)

        semantic_ir = SemanticIR(root=root)
        results = list(semantic_ir.dfs(with_depth=True))

        assert len(results) == 2
        assert results[0] == (root, 0)
        assert results[1] == (div, 1)

    def test_dfs_with_path(self):
        """Test DFS traversal with path."""
        elem1 = SemanticElement(tag="body", readable_id="body-1")
        elem2 = SemanticElement(tag="div", readable_id="div-1")

        root = SemanticTreeNode(data=elem1)
        div = SemanticTreeNode(data=elem2)

        root.add_child(div)

        semantic_ir = SemanticIR(root=root)
        results = list(semantic_ir.dfs(with_path=True))

        assert len(results) == 2
        node1, depth1, path1 = results[0]
        node2, depth2, path2 = results[1]

        assert node1 is root
        assert depth1 == 0
        assert path1 == []

        assert node2 is div
        assert depth2 == 1
        assert path2 == ["body-1"]

    def test_serialize_to_markdown_simple(self):
        """Test markdown serialization."""
        elem1 = SemanticElement(tag="body", readable_id="body-1")
        elem2 = SemanticElement(tag="button", readable_id="button-1", semantic_attributes={"type": "submit"})
        text = SemanticText(text="Click")

        root = SemanticTreeNode(data=elem1)
        button = SemanticTreeNode(data=elem2)
        text_node = SemanticTreeNode(data=text)

        root.add_child(button)
        button.add_child(text_node)

        semantic_ir = SemanticIR(root=root)
        markdown = semantic_ir.serialize_to_markdown()

        assert "- body-1" in markdown
        assert "- button-1" in markdown
        assert '"Click"' in markdown
        assert 'type="submit"' in markdown

    def test_to_dict_simple(self):
        """Test serializing simple tree to dict."""
        elem = SemanticElement(tag="div", readable_id="div-1", semantic_attributes={"class": "test"})
        root = SemanticTreeNode(data=elem)

        semantic_ir = SemanticIR(root=root)
        result = semantic_ir.to_dict()

        assert result['total_nodes'] == 1
        assert result['root']['type'] == 'element'
        assert result['root']['tag'] == 'div'
        assert result['root']['readable_id'] == 'div-1'
        assert result['root']['attributes'] == {"class": "test"}
        assert result['root']['children'] == []

    def test_to_dict_with_children(self):
        """Test serializing tree with children to dict."""
        root = SemanticTreeNode(data=SemanticElement(tag="div"))
        text = SemanticTreeNode(data=SemanticText(text="Hello"))
        p = SemanticTreeNode(data=SemanticElement(tag="p"))

        root.add_child(text)
        root.add_child(p)

        semantic_ir = SemanticIR(root=root)
        result = semantic_ir.to_dict()

        assert result['total_nodes'] == 2  # div and p (not text)
        assert len(result['root']['children']) == 2
        assert result['root']['children'][0]['type'] == 'text'
        assert result['root']['children'][0]['text'] == 'Hello'
        assert result['root']['children'][1]['type'] == 'element'
        assert result['root']['children'][1]['tag'] == 'p'

    def test_semantic_ir_repr(self):
        """Test SemanticIR string representation."""
        root = SemanticTreeNode(data=SemanticElement(tag="body"))
        div = SemanticTreeNode(data=SemanticElement(tag="div"))
        root.add_child(div)

        semantic_ir = SemanticIR(root=root)
        repr_str = repr(semantic_ir)

        assert "SemanticIR" in repr_str
        assert "body" in repr_str
        assert "2" in repr_str  # 2 nodes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
