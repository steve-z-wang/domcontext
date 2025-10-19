# domcontext

Parse DOM trees into clean, LLM-friendly context.

Converts messy HTML/CDP snapshots into structured markdown for LLM context windows. Built on [domnode](https://github.com/steve-z-wang/domnode) for DOM parsing and filtering.

[![Tests](https://img.shields.io/badge/tests-16%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.8+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()
[![Version](https://img.shields.io/badge/version-0.2.0-orange)]()

---

## Quick Start

```python
from domcontext import DomContext

html = """
<html>
<head><title>Example</title></head>
<body>
    <nav><a href="/home">Home</a></nav>
    <main>
        <button type="submit">Search</button>
    </main>
</body>
</html>
"""

# Create DOM context
context = DomContext.from_html(html)

# Get markdown representation
print(context.markdown)
print(f"Tokens: {context.tokens}")

# Access elements by ID
button = context.get_element('button-1')
print(f"Button: {button.tag} - {button.text}")
```

**Output:**
```
- body-1
  - nav-1
    - a-1 (href="/home")
      - "Home"
  - main-1
    - button-1 (type="submit")
      - "Search"

Tokens: 42
Button: button - Search
```

---

## Installation

```bash
pip install domcontext
```

Or from source:

```bash
# Basic installation
pip install -e .

# With dev dependencies
pip install -e ".[dev]"

# With Playwright support
pip install -e ".[playwright]"
playwright install chromium
```

---

## Features

- Semantic filtering - Removes scripts, styles, hidden elements
- Token reduction - 60% average reduction in token count
- Structure preservation - Maintains DOM hierarchy
- Element lookup - Access elements by generated IDs
- Token counting - Built-in tiktoken support
- Configurable filtering - Fine-tune visibility and semantic filters
- Multiple inputs - HTML strings and CDP snapshots
- Smart chunking - Split large DOMs with continuation markers

---

## Usage

### Parse HTML

```python
from domcontext import DomContext

html = '<div><button>Click me</button></div>'
context = DomContext.from_html(html)

print(context.markdown)
# Output:
# - div-1
#   - button-1
#     - "Click me"
```

### Parse CDP Snapshot

```python
from domcontext import DomContext

# From Playwright/Puppeteer
cdp_data = await page.cdp_session.send('DOMSnapshot.captureSnapshot', {
    'computedStyles': [],
    'includeDOMRects': True
})

context = DomContext.from_cdp(cdp_data)
print(context.markdown)
```

### Access Elements

```python
# Get element by ID
button = context.get_element('button-1')
print(button.tag)          # 'button'
print(button.text)         # 'Click me'
print(button.attributes)   # {'type': 'submit'}
print(button.semantic_id)  # 'button-1'

# Get all elements of a type
buttons = context.elements(tag='button')
for btn in buttons:
    print(btn.semantic_id, btn.text)

# Iterate all elements
for element in context:
    print(element.tag, element.semantic_id)
```

### Chunking

```python
# Split into chunks for RAG
chunks = context.chunks(
    max_tokens=500,
    overlap=50,
    include_parent_path=True
)

for chunk in chunks:
    print(f"Chunk ({chunk.tokens} tokens):")
    print(chunk.markdown)
    print("---")
```

### Token Counting

```python
print(f"Tokens: {context.tokens}")

# Use custom tokenizer
from domcontext import TiktokenTokenizer

tokenizer = TiktokenTokenizer(model="gpt-4")
context = DomContext.from_html(html, tokenizer=tokenizer)
```

### Filtering Options

```python
# Disable specific filters
context = DomContext.from_html(
    html,
    filter_non_visible_tags=True,   # Remove script, style, head
    filter_css_hidden=True,          # Remove display:none, visibility:hidden
    filter_zero_dimensions=True,     # Remove zero-size elements
    filter_attributes=True,          # Keep only semantic attributes
    filter_empty=True,               # Remove empty nodes
    collapse_wrappers=True           # Collapse single-child wrappers
)
```

---

## Architecture

Built on the [domnode](https://github.com/steve-z-wang/domnode) library for core DOM operations.

**Pipeline:**

1. **Parse** - HTML/CDP to domnode.Node tree (via domnode)
2. **Filter** - Apply visibility and semantic filters (via domnode)
3. **Enhance** - Add semantic IDs (button-1, input-2, etc.)
4. **Serialize** - Convert to markdown/JSON for LLM context

**Dependencies:**

- **domnode** - DOM parsing, filtering, and tree operations
- **tiktoken** - Token counting for LLM context windows

---

## API Reference

### DomContext

**Class Methods:**
- `DomContext.from_html(html, **filters)` - Parse HTML string
- `DomContext.from_cdp(cdp_data, **filters)` - Parse CDP snapshot

**Properties:**
- `context.markdown` - Markdown representation (cached)
- `context.tokens` - Token count (cached)

**Methods:**
- `context.get_element(id)` - Get element by semantic ID
- `context.elements(tag=None)` - Get all elements, optionally filtered by tag
- `context.chunks(max_tokens, overlap, include_parent_path)` - Split into chunks

### DomNode

Wrapper around domnode.Node with additional properties:

- `node.tag` - HTML tag name
- `node.text` - Text content
- `node.attributes` - Element attributes
- `node.semantic_id` - Generated ID (button-1, input-2, etc.)
- `node.backend_node_id` - CDP backend node ID (if from CDP)
- `node.parent` - Parent element
- `node.children` - Child elements

### Chunk

- `chunk.markdown` - Chunk markdown content
- `chunk.tokens` - Token count

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=domcontext --cov-report=html
```

**Test Coverage:**
- 16 integration tests covering public API
- HTML and CDP parsing
- Filtering pipeline
- Element access
- Chunking and tokenization

---

## Use Cases

**Web Automation**
Provide clean DOM context to LLM agents for element selection and interaction.

**RAG for Websites**
Build vector indexes from web pages with proper chunking and semantic structure.

**Content Extraction**
Extract only visible, meaningful content from complex web pages.

**Testing**
Validate web page structure and content for automated testing.

---

## License

MIT

---

## Related Projects

- [domnode](https://github.com/steve-z-wang/domnode) - DOM parsing and filtering library
- [natural-selector](https://github.com/steve-z-wang/natural-selector) - Natural language element selection with RAG

---

## Changelog

### 0.2.0 (2025-01-19)
- **Breaking:** Migrated to domnode library for core DOM operations
- Eliminated ~1000 lines of duplicate parser/filter code
- Simplified architecture from 3 layers to 1 (domnode.Node)
- Maintained full backward compatibility in public API
- All 16 integration tests passing

### 0.1.3 (2025-01-18)
- Improved chunking with continuation markers
- Better handling of deeply nested structures
- 188 unit tests covering internal implementation

### 0.1.0 (2025-01-15)
- Initial release
- HTML and CDP parsing
- Visibility and semantic filtering
- Markdown serialization
- Token counting
