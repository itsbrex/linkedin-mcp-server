# linkedin_mcp_server/bridge/client.py
"""
Chrome Bridge HTTP/WebSocket client for communicating with mcp-chrome-bridge.

Provides low-level API communication with the bridge server including session
management, navigation, script execution, and cookie handling.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class BridgeConnectionError(Exception):
    """Raised when bridge connection fails."""
    pass


class BridgeSessionError(Exception):
    """Raised when bridge session operation fails."""
    pass


class BridgeClient:
    """HTTP client for mcp-chrome-bridge communication."""

    def __init__(self, bridge_url: str = "http://localhost:3000", timeout: int = 30):
        self.bridge_url = bridge_url.rstrip('/')
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def _request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make HTTP request to bridge server."""
        url = f"{self.bridge_url}{endpoint}"
        session = await self._get_session()
        
        try:
            logger.debug(f"Bridge request: {method} {url}")
            
            if method.upper() == "GET":
                async with session.get(url) as response:
                    response.raise_for_status()
                    result = await response.json()
            else:
                async with session.request(method, url, json=data) as response:
                    response.raise_for_status()
                    result = await response.json()
            
            logger.debug(f"Bridge response: {result}")
            return result
            
        except aiohttp.ClientError as e:
            logger.error(f"Bridge request failed: {e}")
            raise BridgeConnectionError(f"Failed to connect to bridge at {url}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from bridge: {e}")
            raise BridgeConnectionError(f"Invalid response from bridge: {e}")

    async def health_check(self) -> bool:
        """Check if bridge server is available."""
        try:
            await self._request("GET", "/health")
            return True
        except BridgeConnectionError:
            return False

    async def create_session(self, profile_name: str = "default", headless: bool = True) -> str:
        """Create a new Chrome session via bridge."""
        data = {
            "profileName": profile_name,
            "headless": headless,
            "userDataDir": f"/tmp/chrome-bridge-{profile_name}",  # Default temp directory
        }
        
        try:
            result = await self._request("POST", "/sessions", data)
            session_id = result.get("sessionId")
            
            if not session_id:
                raise BridgeSessionError("Bridge did not return a session ID")
            
            logger.info(f"Created bridge session: {session_id}")
            return session_id
            
        except BridgeConnectionError:
            raise
        except Exception as e:
            raise BridgeSessionError(f"Failed to create bridge session: {e}")

    async def close_session(self, session_id: str) -> None:
        """Close a Chrome session via bridge."""
        try:
            await self._request("DELETE", f"/sessions/{session_id}")
            logger.info(f"Closed bridge session: {session_id}")
        except BridgeConnectionError:
            raise
        except Exception as e:
            raise BridgeSessionError(f"Failed to close bridge session {session_id}: {e}")

    async def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active Chrome sessions."""
        try:
            result = await self._request("GET", "/sessions")
            return result.get("sessions", [])
        except BridgeConnectionError:
            raise
        except Exception as e:
            raise BridgeSessionError(f"Failed to list bridge sessions: {e}")

    async def navigate(self, session_id: str, url: str) -> None:
        """Navigate to URL in the specified session."""
        data = {"url": url}
        
        try:
            await self._request("POST", f"/sessions/{session_id}/navigate", data)
            logger.debug(f"Navigated session {session_id} to {url}")
        except BridgeConnectionError:
            raise
        except Exception as e:
            raise BridgeSessionError(f"Failed to navigate session {session_id} to {url}: {e}")

    async def execute_script(self, session_id: str, script: str) -> Any:
        """Execute JavaScript in the specified session."""
        data = {"script": script}
        
        try:
            result = await self._request("POST", f"/sessions/{session_id}/execute", data)
            return result.get("result")
        except BridgeConnectionError:
            raise
        except Exception as e:
            raise BridgeSessionError(f"Failed to execute script in session {session_id}: {e}")

    async def get_cookies(self, session_id: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get cookies from the specified session."""
        endpoint = f"/sessions/{session_id}/cookies"
        if domain:
            endpoint += f"?domain={domain}"
        
        try:
            result = await self._request("GET", endpoint)
            return result.get("cookies", [])
        except BridgeConnectionError:
            raise
        except Exception as e:
            raise BridgeSessionError(f"Failed to get cookies from session {session_id}: {e}")

    async def set_cookies(self, session_id: str, cookies: List[Dict[str, Any]]) -> None:
        """Set cookies in the specified session."""
        data = {"cookies": cookies}
        
        try:
            await self._request("POST", f"/sessions/{session_id}/cookies", data)
            logger.debug(f"Set {len(cookies)} cookies in session {session_id}")
        except BridgeConnectionError:
            raise
        except Exception as e:
            raise BridgeSessionError(f"Failed to set cookies in session {session_id}: {e}")

    async def get_page_source(self, session_id: str) -> str:
        """Get page source from the specified session."""
        try:
            result = await self._request("GET", f"/sessions/{session_id}/source")
            return result.get("source", "")
        except BridgeConnectionError:
            raise
        except Exception as e:
            raise BridgeSessionError(f"Failed to get page source from session {session_id}: {e}")

    async def get_current_url(self, session_id: str) -> str:
        """Get current URL from the specified session."""
        try:
            result = await self._request("GET", f"/sessions/{session_id}/url")
            return result.get("url", "")
        except BridgeConnectionError:
            raise
        except Exception as e:
            raise BridgeSessionError(f"Failed to get current URL from session {session_id}: {e}")

    async def close(self) -> None:
        """Close the HTTP client session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("Closed bridge HTTP client session")