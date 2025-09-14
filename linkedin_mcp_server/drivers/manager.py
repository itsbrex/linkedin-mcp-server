# linkedin_mcp_server/drivers/manager.py
"""
Browser session manager that provides unified access to Chrome WebDriver or Bridge sessions.

This module provides a high-level interface for managing browser sessions that can
operate through either direct Chrome WebDriver or the Chrome Bridge transport layer.
It handles session lifecycle, authentication, and automatic fallback between modes.
"""

import asyncio
import logging
from typing import Optional, Union

from selenium import webdriver

from linkedin_mcp_server.bridge import ChromeBridgeAdapter, BridgeSession
from linkedin_mcp_server.bridge.session import BrowserSession, ChromeSession
from linkedin_mcp_server.bridge.client import BridgeConnectionError, BridgeSessionError
from linkedin_mcp_server.config import get_config
from linkedin_mcp_server.drivers.chrome import get_or_create_driver as get_chrome_driver

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages browser sessions with automatic bridge/selenium selection."""

    def __init__(self):
        self.config = get_config()
        self._bridge_adapter: Optional[ChromeBridgeAdapter] = None
        self._current_session: Optional[Union[BridgeSession, webdriver.Chrome]] = None
        self._current_browser_session: Optional[BrowserSession] = None

    async def _get_bridge_adapter(self) -> ChromeBridgeAdapter:
        """Get or create bridge adapter."""
        if self._bridge_adapter is None:
            self._bridge_adapter = ChromeBridgeAdapter(
                bridge_url=self.config.bridge.url,
                timeout=self.config.bridge.timeout
            )
        return self._bridge_adapter

    async def _try_bridge_session(self, authentication: str) -> Optional[BrowserSession]:
        """Try to create a bridge session."""
        if not self.config.bridge.enabled:
            logger.debug("Bridge mode disabled in configuration")
            return None

        try:
            bridge_adapter = await self._get_bridge_adapter()
            
            # Check if bridge is available
            if not await bridge_adapter.is_available():
                logger.warning("Chrome Bridge server is not available")
                if not self.config.bridge.fallback_to_selenium:
                    raise BridgeConnectionError("Bridge unavailable and fallback disabled")
                return None

            # Create authenticated bridge session
            bridge_session = await bridge_adapter.get_or_create_session(
                profile_name=self.config.bridge.profile_name,
                authentication=authentication
            )

            self._current_session = bridge_session
            browser_session = bridge_session.get_browser_session()
            
            logger.info(f"Using Chrome Bridge session (profile: {self.config.bridge.profile_name})")
            return browser_session

        except (BridgeConnectionError, BridgeSessionError) as e:
            logger.warning(f"Failed to create bridge session: {e}")
            if not self.config.bridge.fallback_to_selenium:
                raise
            return None

    def _get_selenium_session(self, authentication: str) -> BrowserSession:
        """Create a Selenium WebDriver session."""
        logger.info("Creating Selenium WebDriver session")
        
        # Use existing Chrome driver logic
        driver = get_chrome_driver(authentication)
        self._current_session = driver
        
        browser_session = ChromeSession(driver)
        logger.info("Using direct Chrome WebDriver session")
        return browser_session

    async def get_session(self, authentication: str) -> BrowserSession:
        """
        Get browser session using bridge or selenium fallback.
        
        Args:
            authentication: LinkedIn session cookie
            
        Returns:
            BrowserSession: Either bridge or direct WebDriver session
            
        Raises:
            Exception: If both bridge and fallback fail
        """
        # Close any existing session first
        await self.close_session()

        # Try bridge first if enabled
        browser_session = await self._try_bridge_session(authentication)
        
        if browser_session is None:
            # Fall back to direct Selenium
            if self.config.bridge.enabled and not self.config.bridge.fallback_to_selenium:
                raise RuntimeError("Bridge mode enabled but unavailable, and fallback disabled")
            
            browser_session = self._get_selenium_session(authentication)

        self._current_browser_session = browser_session
        return browser_session

    async def close_session(self) -> None:
        """Close the current browser session."""
        if self._current_browser_session:
            await self._current_browser_session.close()
            self._current_browser_session = None

        if self._current_session:
            if isinstance(self._current_session, BridgeSession):
                await self._current_session.close()
            elif isinstance(self._current_session, webdriver.Chrome):
                try:
                    self._current_session.quit()
                except Exception as e:
                    logger.warning(f"Error closing Chrome driver: {e}")
            
            self._current_session = None

        logger.info("Browser session closed")

    async def close_all(self) -> None:
        """Close all sessions and adapters."""
        await self.close_session()
        
        if self._bridge_adapter:
            await self._bridge_adapter.close()
            self._bridge_adapter = None

    def get_current_session(self) -> Optional[BrowserSession]:
        """Get the current browser session if available."""
        return self._current_browser_session

    def is_bridge_mode(self) -> bool:
        """Check if currently using bridge mode."""
        return (self._current_browser_session is not None and 
                self._current_browser_session.is_bridge_session())


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create the global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


async def get_browser_session(authentication: str) -> BrowserSession:
    """
    Get a browser session with automatic bridge/selenium selection.
    
    Args:
        authentication: LinkedIn session cookie
        
    Returns:
        BrowserSession: Ready-to-use browser session
    """
    manager = get_session_manager()
    return await manager.get_session(authentication)


async def close_all_sessions() -> None:
    """Close all browser sessions and clean up resources."""
    global _session_manager
    if _session_manager:
        await _session_manager.close_all()
        _session_manager = None


def get_current_browser_session() -> Optional[BrowserSession]:
    """Get current browser session without creating a new one."""
    global _session_manager
    if _session_manager:
        return _session_manager.get_current_session()
    return None