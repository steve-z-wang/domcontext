# domcontext

**Parse DOM trees into clean, LLM-friendly context.**

Converts messy HTML/CDP snapshots into structured markdown for LLM context windows. Designed for web automation agents that need to provide clean DOM context to LLMs.

> **⚠️ Development Status:** This package is in active development (v0.1.x). APIs may change between minor versions. Not recommended for production use yet.

> **Why "domcontext"?** It's a double pun! 🎯
> - **DOM** (Document Object Model) + **context** (LLM context windows)
> - Provides **DOM context** for your LLM agents

[![Tests](https://img.shields.io/badge/tests-173%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.8+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()
[![Version](https://img.shields.io/badge/version-0.1.2--alpha-orange)]()

---

## Quick Start

```python
from domcontext import DomContext

# Parse HTML string
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

# Iterate through interactive elements
for element in context.elements():
    print(f"{element.id}: {element.tag} - {element.text}")
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
```

---

## Installation

```bash
# Install from source
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Install with Playwright support (for live browser CDP capture)
pip install -e ".[playwright]"

# Install with Jupyter notebooks support (to run examples)
pip install -e ".[examples,playwright]"

# Install with all optional dependencies
pip install -e ".[dev,playwright,examples]"
```

After installing with Playwright support, install browser binaries:
```bash
playwright install chromium
```

---

## Features

- 🧹 **Semantic filtering** - Removes scripts, styles, hidden elements automatically
- 📉 **Token reduction** - 60% average reduction in token count
- 🎯 **Structure preservation** - Maintains DOM hierarchy in clean format
- 🔍 **Element lookup** - Access original DOM elements by their generated IDs
- 📊 **Token counting** - Built-in token counting with tiktoken
- 🎛️ **Configurable filtering** - Fine-tune visibility and semantic filters
- 📦 **Multiple input formats** - Support for HTML strings and CDP snapshots
- 🧩 **Smart chunking** - Split large DOMs into context-sized chunks with configurable overlap

---

## API

### Parse HTML

```python
from domcontext import DomContext

# Basic parsing
context = DomContext.from_html(html_string)

# With custom filter options
context = DomContext.from_html(
    html_string,
    filter_non_visible=True,      # Remove script, style tags
    filter_css_hidden=True,        # Remove display:none, visibility:hidden
    filter_zero_dimensions=True,   # Remove zero-width/height elements
    filter_empty_elements=True,    # Remove empty wrapper divs
    filter_attributes=True,        # Keep only semantic attributes
    collapse_wrappers=True         # Collapse single-child wrappers
)
```

### Parse CDP Snapshot

```python
# From Chrome DevTools Protocol snapshot
cdp_snapshot = {
    'documents': [...],
    'strings': [...]
}

context = DomContext.from_cdp(cdp_snapshot)
```

### Access Context

```python
# Markdown representation
markdown = context.markdown

# Token count
token_count = context.tokens

# Get all interactive elements
for element in context.elements():
    print(f"ID: {element.id}")
    print(f"Tag: {element.tag}")
    print(f"Text: {element.text}")
    print(f"Attributes: {element.attributes}")

# Get element by ID
element = context.get_element("button-1")
print(element.attributes)  # {'type': 'submit'}

# Get as dictionary
data = context.to_dict()
```

### Chunking

```python
# Split large DOMs into chunks
for chunk in context.chunks(max_tokens=1000, overlap=100):
    print(f"Chunk tokens: {chunk.tokens}")
    print(chunk.markdown)
```

### Custom Tokenizer

```python
from domcontext import DomContext, Tokenizer

class CustomTokenizer(Tokenizer):
    def count_tokens(self, text: str) -> int:
        # Your custom token counting logic
        return len(text.split())

context = DomContext.from_html(html, tokenizer=CustomTokenizer())
```

### Playwright Utilities (Optional)

Capture CDP snapshots directly from live browser sessions:

```python
from playwright.async_api import async_playwright
from domcontext import DomContext
from domcontext.utils import capture_snapshot

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://example.com')

        # Capture CDP snapshot from live page
        snapshot = await capture_snapshot(page)

        # Parse into DomContext
        context = DomContext.from_cdp(snapshot)
        print(context.markdown)

        await browser.close()

# Run with: python -m asyncio script.py
```

**Note:** Requires installation with `pip install domcontext[playwright]`

---

## Architecture

The library uses a multi-stage filtering pipeline:

1. **Parse** - HTML/CDP → DomIR (complete DOM tree with all data)
2. **Visibility Filter** - Remove non-visible elements (optional flags)
   - Non-visible tags (script, style, head)
   - CSS hidden elements (display:none, visibility:hidden)
   - Zero-dimension elements
3. **Semantic Filter** - Extract semantic information (optional flags)
   - Convert to SemanticIR
   - Filter to semantic attributes only
   - Remove empty nodes
   - Collapse wrapper divs
   - Generate readable IDs
4. **Output** - SemanticIR → Markdown/JSON

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=domcontext --cov-report=html

# Run specific test suite
pytest tests/unit/parsers/
pytest tests/unit/filters/
pytest tests/unit/ir/
```

**Test Coverage:**
- 173 tests passing
- HTML Parser (13 tests)
- CDP Parser (12 tests)
- DomIR Layer (27 tests)
- SemanticIR Layer (34 tests)
- Visibility Filters (43 tests)
- Semantic Filters (28 tests)
- Tokenizers (13 tests)

---

## Use Cases

- **Web automation agents** - Provide clean DOM context to LLMs for element selection
- **Web scraping** - Extract structured content from complex pages
- **Testing** - Generate clean snapshots of DOM state
- **Accessibility** - Extract semantic structure from pages

---

## License

MIT

---

## Examples

Check out the interactive Jupyter notebooks in `examples/`:

- **`simple_demo.ipynb`** - Quick start guide with Google search example
  - Element lookup by ID
  - Chunking demonstration
  - Perfect for beginners

- **`advanced_demo.ipynb`** - Advanced features showcase
  - Custom filters and tokenizers
  - Element iteration and statistics
  - LLM prompt generation
  - Production patterns

Run with:
```bash
jupyter notebook examples/simple_demo.ipynb
```

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/

# Lint
ruff check src/ tests/
```

---

## TODO

### Chunking Improvements

1. **Handle super long text nodes** - Improve chunk behavior when a single text element exceeds the max token limit. Currently, if a single text node is larger than `max_tokens`, it will be placed in its own chunk, potentially exceeding the limit. Future improvement: split long text nodes across multiple chunks while preserving context.

### Collapsing Improvements

2. **Collapse text-wrapping elements** - Improve wrapper collapsing to also collapse elements that only wrap text (not just elements that wrap other elements). Currently, `<a><span>text</span></a>` keeps the `span`, but it should be collapsed to `<a>text</a>` if the span has no attributes. Exception: Don't collapse interactive elements (button, input, a, select, textarea, etc.) even when they only wrap text, as these are semantically meaningful.

### Evaluation & Benchmarking

3. **Mind2Web dataset evaluation** - Conduct comprehensive testing on the [Mind2Web dataset](https://osu-nlp-group.github.io/Mind2Web/) to evaluate DOM context quality, token reduction rates, and element selection accuracy across diverse real-world websites. Report will include performance metrics, edge cases discovered, and comparison with baseline HTML parsing.

---

## Contributing

Contributions welcome! Please ensure tests pass and add new tests for new features.

```bash
# Run full test suite
pytest -v

# Check coverage
pytest --cov=domcontext
```
