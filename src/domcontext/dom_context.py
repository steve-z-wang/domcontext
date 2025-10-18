"""DomContext - Public API for parsed DOM pages."""

from typing import List, Optional, Iterator, Dict, Any, Tuple
from ._internal.ir.dom_ir import DomIR
from ._internal.ir.semantic_ir import SemanticIR
from .dom_node import DomNode
from ._internal.chunker import chunk_semantic_ir, Chunk
from .tokenizer import Tokenizer, TiktokenTokenizer


class DomContext:
    """Public API for parsed DOM page.

    Provides clean interface for accessing markdown, tokens, and elements.
    Caches expensive operations for performance.
    """

    def __init__(
        self,
        dom_ir: DomIR,
        semantic_ir: SemanticIR,
        tokenizer: Tokenizer
    ):
        """Initialize DomContext.

        Args:
            dom_ir: Complete DOM tree with all CDP data
            semantic_ir: Filtered semantic tree for LLM
            tokenizer: Tokenizer for counting tokens
        """
        self._dom_ir = dom_ir
        self._semantic_ir = semantic_ir
        self._tokenizer = tokenizer

        # Caches
        self._markdown_cache: Optional[str] = None
        self._token_cache: Optional[int] = None
        self._chunks_cache: Dict = {}  # Cache by (size, overlap)

    @classmethod
    def _from_dom_ir(
        cls,
        dom_ir: DomIR,
        tokenizer: Optional[Tokenizer] = None,
        filter_non_visible_tags: bool = True,
        filter_css_hidden: bool = True,
        filter_zero_dimensions: bool = True,
        filter_attributes: bool = True,
        filter_empty: bool = True,
        collapse_wrappers: bool = True
    ) -> 'DomContext':
        """Create DomContext from DomIR through filtering pipeline.

        Args:
            dom_ir: Complete DOM tree
            tokenizer: Optional tokenizer for counting tokens
            filter_non_visible_tags: Remove script, style, head tags
            filter_css_hidden: Remove display:none, visibility:hidden elements
            filter_zero_dimensions: Remove zero-dimension elements
            filter_attributes: Keep only semantic attributes
            filter_empty: Remove empty nodes
            collapse_wrappers: Collapse single-child wrappers

        Returns:
            DomContext with filtered semantic tree
        """
        from ._internal.filters.visibility_pass import visibility_pass
        from ._internal.filters.semantic_pass import semantic_pass

        # Visibility filtering
        filtered_dom_ir = visibility_pass(
            dom_ir,
            filter_non_visible_tags=filter_non_visible_tags,
            filter_css_hidden=filter_css_hidden,
            filter_zero_dimensions=filter_zero_dimensions
        )
        if filtered_dom_ir is None:
            filtered_dom_ir = dom_ir

        # Semantic filtering
        semantic_ir = semantic_pass(
            filtered_dom_ir,
            filter_attributes=filter_attributes,
            filter_empty=filter_empty,
            collapse_wrappers=collapse_wrappers
        )
        if semantic_ir is None:
            raise ValueError("No semantic elements found")

        # Create tokenizer
        if tokenizer is None:
            tokenizer = TiktokenTokenizer()

        return cls(
            dom_ir=filtered_dom_ir,
            semantic_ir=semantic_ir,
            tokenizer=tokenizer
        )

    @classmethod
    def from_html(
        cls,
        html: str,
        tokenizer: Optional[Tokenizer] = None,
        filter_non_visible_tags: bool = True,
        filter_css_hidden: bool = True,
        filter_zero_dimensions: bool = True,
        filter_attributes: bool = True,
        filter_empty: bool = True,
        collapse_wrappers: bool = True
    ) -> 'DomContext':
        """Parse HTML string into DomContext.

        Args:
            html: HTML string to parse
            tokenizer: Optional tokenizer for counting tokens (default: TiktokenTokenizer())
            filter_non_visible_tags: Remove script, style, head tags (default: True)
            filter_css_hidden: Remove display:none, visibility:hidden elements (default: True)
            filter_zero_dimensions: Remove zero-dimension elements (default: True)
            filter_attributes: Keep only semantic attributes (default: True)
            filter_empty: Remove empty nodes (default: True)
            collapse_wrappers: Collapse single-child wrappers (default: True)

        Returns:
            DomContext with markdown, tokens, and element access

        Example:
            >>> context = DomContext.from_html(html)
            >>> print(context.markdown)
            >>> # Skip certain filters
            >>> context = DomContext.from_html(html, filter_empty=False, collapse_wrappers=False)
        """
        from ._internal.parsers.html_parser import parse_html as html_to_dom_ir

        # Parse HTML to DomIR
        dom_ir = html_to_dom_ir(html)

        return cls._from_dom_ir(
            dom_ir,
            tokenizer=tokenizer,
            filter_non_visible_tags=filter_non_visible_tags,
            filter_css_hidden=filter_css_hidden,
            filter_zero_dimensions=filter_zero_dimensions,
            filter_attributes=filter_attributes,
            filter_empty=filter_empty,
            collapse_wrappers=collapse_wrappers
        )

    @classmethod
    def from_cdp(
        cls,
        cdp_data: Dict[str, Any],
        tokenizer: Optional[Tokenizer] = None,
        filter_non_visible_tags: bool = True,
        filter_css_hidden: bool = True,
        filter_zero_dimensions: bool = True,
        filter_attributes: bool = True,
        filter_empty: bool = True,
        collapse_wrappers: bool = True
    ) -> 'DomContext':
        """Parse CDP data into DomContext.

        Args:
            cdp_data: CDP data dictionary with DOM snapshot
            tokenizer: Optional tokenizer for counting tokens (default: TiktokenTokenizer())
            filter_non_visible_tags: Remove script, style, head tags (default: True)
            filter_css_hidden: Remove display:none, visibility:hidden elements (default: True)
            filter_zero_dimensions: Remove zero-dimension elements (default: True)
            filter_attributes: Keep only semantic attributes (default: True)
            filter_empty: Remove empty nodes (default: True)
            collapse_wrappers: Collapse single-child wrappers (default: True)

        Returns:
            DomContext with markdown, tokens, and element access

        Example:
            >>> context = DomContext.from_cdp(cdp_data)
            >>> print(context.markdown)
            >>> # Skip certain filters
            >>> context = DomContext.from_cdp(cdp_data, filter_empty=False)
        """
        from ._internal.parsers.cdp_parser import parse_cdp_snapshot as cdp_to_dom_ir

        # Parse CDP to DomIR
        dom_ir = cdp_to_dom_ir(cdp_data)

        return cls._from_dom_ir(
            dom_ir,
            tokenizer=tokenizer,
            filter_non_visible_tags=filter_non_visible_tags,
            filter_css_hidden=filter_css_hidden,
            filter_zero_dimensions=filter_zero_dimensions,
            filter_attributes=filter_attributes,
            filter_empty=filter_empty,
            collapse_wrappers=collapse_wrappers
        )

    @property
    def markdown(self) -> str:
        """Clean markdown representation (cached).

        Returns:
            Markdown string with bullet-list format
        """
        if self._markdown_cache is None:
            self._markdown_cache = self._semantic_ir.serialize_to_markdown()
        return self._markdown_cache

    @property
    def tokens(self) -> int:
        """Token count using tiktoken (cached).

        Returns:
            Number of tokens in markdown representation
        """
        if self._token_cache is None:
            self._token_cache = self._tokenizer.count_tokens(self.markdown)
        return self._token_cache

    def chunks(self, max_tokens: int = 500, overlap: int = 50, include_parent_path: bool = True) -> List[Chunk]:
        """Split into chunks with specified max tokens and overlap (cached).

        Args:
            max_tokens: Maximum chunk size in tokens (default: 500)
            overlap: Overlap between chunks in tokens (default: 50)
            include_parent_path: Include parent path and continuation indicators (default: True)

        Returns:
            List of Chunk objects with markdown and token count
        """
        cache_key = (max_tokens, overlap, include_parent_path)
        if cache_key not in self._chunks_cache:
            self._chunks_cache[cache_key] = chunk_semantic_ir(
                self._semantic_ir,
                self._tokenizer,
                size=max_tokens,
                overlap=overlap,
                include_parent_path=include_parent_path
            )
        return self._chunks_cache[cache_key]

    def get_element(self, element_id: str) -> DomNode:
        """Get element by its readable ID.

        Args:
            element_id: Readable ID like "button-1", "input-2"

        Returns:
            DomNode wrapping the element

        Raises:
            KeyError: If element ID not found
        """
        semantic_element = self._semantic_ir.get_element_by_id(element_id)
        if semantic_element is None:
            raise KeyError(f"Element '{element_id}' not found")

        if semantic_element.dom_tree_node is None:
            raise ValueError(f"Element '{element_id}' has no DOM tree reference")

        return DomNode(semantic_element.dom_tree_node)

    def elements(self, tag: Optional[str] = None) -> List[DomNode]:
        """Get all elements, optionally filtered by tag.

        Args:
            tag: Optional tag name to filter by (e.g., "button", "input")

        Returns:
            List of DomNode objects
        """
        result = []
        all_elements = self._semantic_ir.get_all_elements_with_ids()

        for element in all_elements.values():
            if tag is None or element.tag == tag:
                if element.dom_tree_node is not None:
                    result.append(DomNode(element.dom_tree_node))

        return result

    def __iter__(self) -> Iterator[DomNode]:
        """Iterate over all elements in document order.

        Yields:
            DomNode objects in DFS order
        """
        from ._internal.ir.semantic_ir import SemanticElement

        for node in self._semantic_ir.dfs():
            # Only yield element nodes, not text nodes
            if isinstance(node.data, SemanticElement) and node.data.dom_tree_node is not None:
                yield DomNode(node.data.dom_tree_node)

    def __repr__(self) -> str:
        return f'DomContext(elements={len(self._semantic_ir.all_element_nodes())}, tokens={self.tokens})'

    def __str__(self) -> str:
        return self.markdown
