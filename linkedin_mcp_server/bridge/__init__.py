# linkedin_mcp_server/bridge/__init__.py
"""
MCP Chrome Bridge integration module.

This module provides the Chrome Bridge transport layer for seamless Chrome session reuse
via the mcp-chrome-bridge package. It enables the LinkedIn MCP server to operate through
a user's existing Chrome profile without requiring manual cookie setup or separate 
Playwright instances.
"""

from .adapter import ChromeBridgeAdapter, BridgeSession
from .session import BrowserSession, ChromeSession, BridgeSessionImpl
from .client import BridgeClient

__all__ = [
    "ChromeBridgeAdapter",
    "BridgeSession", 
    "BrowserSession",
    "ChromeSession",
    "BridgeSessionImpl",
    "BridgeClient",
]