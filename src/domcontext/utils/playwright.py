"""Playwright utilities for capturing CDP snapshots.

This module requires the optional 'playwright' dependency.
Install with: pip install domcontext[playwright]
"""

from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page

# Check if playwright is installed
try:
    import playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


async def capture_snapshot(page: 'Page') -> Dict[str, Any]:
    """
    Capture CDP DOMSnapshot from a Playwright page.

    This function captures a complete DOM snapshot including:
    - DOM structure with all nodes
    - Computed styles (display, visibility, opacity)
    - Layout information (bounding boxes)
    - Paint order for rendering

    Args:
        page: Playwright Page object from an active browser session

    Returns:
        Dict containing CDP DOMSnapshot with:
            - documents: List of document snapshots
            - strings: Shared string table for efficient storage

    Raises:
        ImportError: If playwright is not installed

    Example:
        ```python
        from playwright.async_api import async_playwright
        from domcontext import DomContext
        from domcontext.utils import capture_snapshot

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto('https://example.com')

            # Capture CDP snapshot
            snapshot = await capture_snapshot(page)

            # Parse into DomContext
            context = DomContext.from_cdp(snapshot)
            print(context.markdown)

            await browser.close()
        ```
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise ImportError(
            "Playwright is not installed. "
            "Install it with: pip install domcontext[playwright]"
        )

    # Get CDP session from the page
    cdp = await page.context.new_cdp_session(page)

    # Capture snapshot with full layout and style information
    snapshot = await cdp.send('DOMSnapshot.captureSnapshot', {
        'computedStyles': ['display', 'visibility', 'opacity'],  # Styles for visibility filtering
        'includePaintOrder': True,    # Include rendering order
        'includeDOMRects': True        # Include bounding boxes
    })

    return snapshot


async def capture_snapshot_with_html(page: 'Page') -> tuple[Dict[str, Any], str]:
    """
    Capture both CDP snapshot and raw HTML from a Playwright page.

    Useful for debugging or comparing CDP vs HTML parsing.

    Args:
        page: Playwright Page object

    Returns:
        Tuple of (cdp_snapshot, html_string)

    Raises:
        ImportError: If playwright is not installed

    Example:
        ```python
        snapshot, html = await capture_snapshot_with_html(page)

        # Compare both parsing methods
        context_cdp = DomContext.from_cdp(snapshot)
        context_html = DomContext.from_html(html)
        ```
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise ImportError(
            "Playwright is not installed. "
            "Install it with: pip install domcontext[playwright]"
        )

    # Capture both simultaneously
    snapshot = await capture_snapshot(page)
    html = await page.content()

    return snapshot, html
