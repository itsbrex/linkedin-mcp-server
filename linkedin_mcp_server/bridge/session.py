# linkedin_mcp_server/bridge/session.py
"""
Browser session abstraction layer for LinkedIn MCP server.

Provides a unified interface for browser operations that can be implemented
by both direct Chrome WebDriver and Chrome Bridge transport layers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from selenium import webdriver

logger = logging.getLogger(__name__)


class BrowserSession(ABC):
    """Abstract base class for browser session implementations."""

    @abstractmethod
    async def navigate(self, url: str) -> None:
        """Navigate to the specified URL."""
        pass

    @abstractmethod
    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript code in the browser."""
        pass

    @abstractmethod
    async def get_cookies(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get cookies for the specified domain."""
        pass

    @abstractmethod
    async def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """Set cookies in the browser."""
        pass

    @abstractmethod
    async def get_page_source(self) -> str:
        """Get the HTML source of the current page."""
        pass

    @abstractmethod
    async def get_current_url(self) -> str:
        """Get the current page URL."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the browser session."""
        pass

    @abstractmethod
    def is_bridge_session(self) -> bool:
        """Return True if this is a bridge session, False if direct WebDriver."""
        pass


class ChromeSession(BrowserSession):
    """Chrome WebDriver session implementation."""

    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self._closed = False

    async def navigate(self, url: str) -> None:
        """Navigate to the specified URL using WebDriver."""
        if self._closed:
            raise RuntimeError("Session has been closed")
        
        logger.debug(f"Navigating to: {url}")
        self.driver.get(url)

    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript using WebDriver."""
        if self._closed:
            raise RuntimeError("Session has been closed")
        
        return self.driver.execute_script(script)

    async def get_cookies(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get cookies using WebDriver."""
        if self._closed:
            raise RuntimeError("Session has been closed")
        
        all_cookies = self.driver.get_cookies()
        
        if domain:
            return [cookie for cookie in all_cookies if cookie.get('domain', '').endswith(domain)]
        
        return all_cookies

    async def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """Set cookies using WebDriver."""
        if self._closed:
            raise RuntimeError("Session has been closed")
        
        for cookie in cookies:
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                logger.warning(f"Failed to set cookie {cookie.get('name', 'unknown')}: {e}")

    async def get_page_source(self) -> str:
        """Get page source using WebDriver."""
        if self._closed:
            raise RuntimeError("Session has been closed")
        
        return self.driver.page_source

    async def get_current_url(self) -> str:
        """Get current URL using WebDriver."""
        if self._closed:
            raise RuntimeError("Session has been closed")
        
        return self.driver.current_url

    async def close(self) -> None:
        """Close the WebDriver session."""
        if not self._closed:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing Chrome driver: {e}")
            finally:
                self._closed = True

    def is_bridge_session(self) -> bool:
        """Return False since this is a direct WebDriver session."""
        return False


class BridgeSessionImpl(BrowserSession):
    """Chrome Bridge session implementation."""

    def __init__(self, session_id: str, bridge_client: 'BridgeClient'):
        self.session_id = session_id
        self.bridge_client = bridge_client
        self._closed = False

    async def navigate(self, url: str) -> None:
        """Navigate using bridge client."""
        if self._closed:
            raise RuntimeError("Session has been closed")
        
        logger.debug(f"Bridge navigating to: {url}")
        await self.bridge_client.navigate(self.session_id, url)

    async def execute_script(self, script: str) -> Any:
        """Execute JavaScript using bridge client."""
        if self._closed:
            raise RuntimeError("Session has been closed")
        
        return await self.bridge_client.execute_script(self.session_id, script)

    async def get_cookies(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get cookies using bridge client."""
        if self._closed:
            raise RuntimeError("Session has been closed")
        
        return await self.bridge_client.get_cookies(self.session_id, domain)

    async def set_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """Set cookies using bridge client."""
        if self._closed:
            raise RuntimeError("Session has been closed")
        
        await self.bridge_client.set_cookies(self.session_id, cookies)

    async def get_page_source(self) -> str:
        """Get page source using bridge client."""
        if self._closed:
            raise RuntimeError("Session has been closed")
        
        return await self.bridge_client.get_page_source(self.session_id)

    async def get_current_url(self) -> str:
        """Get current URL using bridge client."""
        if self._closed:
            raise RuntimeError("Session has been closed")
        
        return await self.bridge_client.get_current_url(self.session_id)

    async def close(self) -> None:
        """Close the bridge session."""
        if not self._closed:
            try:
                await self.bridge_client.close_session(self.session_id)
            except Exception as e:
                logger.warning(f"Error closing bridge session {self.session_id}: {e}")
            finally:
                self._closed = True

    def is_bridge_session(self) -> bool:
        """Return True since this is a bridge session."""
        return True