"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def simple_html():
    """Simple HTML for basic testing."""
    return """
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Hello World</h1>
        <p>This is a test.</p>
    </body>
    </html>
    """


@pytest.fixture
def nested_html():
    """Nested HTML structure."""
    return """
    <html>
    <body>
        <div>
            <div>
                <div>
                    <p>Deeply nested</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def form_html():
    """HTML with form elements."""
    return """
    <html>
    <body>
        <form>
            <input type="text" placeholder="Username" name="username"/>
            <input type="password" placeholder="Password" name="password"/>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """


@pytest.fixture
def hidden_elements_html():
    """HTML with hidden elements."""
    return """
    <html>
    <head>
        <script>alert('test');</script>
        <style>body { margin: 0; }</style>
    </head>
    <body>
        <div style="display:none">Hidden div</div>
        <div style="visibility:hidden">Invisible div</div>
        <p>Visible paragraph</p>
    </body>
    </html>
    """


@pytest.fixture
def wrapper_html():
    """HTML with wrapper divs."""
    return """
    <html>
    <body>
        <div>
            <a href="/home">Home</a>
        </div>
        <div>
            <div>
                <button>Click</button>
            </div>
        </div>
    </body>
    </html>
    """
