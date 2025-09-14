# linkedin_mcp_server/bridge/adapter.py
"""
Chrome Bridge adapter providing high-level session management.

Manages bridge connections, session lifecycle, authentication, and provides
fallback mechanisms when the bridge is unavailable.
"""

import asyncio
import logging
from typing import Dict, Optional

from .client import BridgeClient, BridgeConnectionError, BridgeSessionError
from .session import BrowserSession, BridgeSessionImpl

logger = logging.getLogger(__name__)


class BridgeSession:
    """High-level bridge session with authentication state."""
    
    def __init__(self, session_id: str, bridge_client: BridgeClient, authenticated: bool = False):
        self.session_id = session_id
        self.bridge_client = bridge_client
        self.authenticated = authenticated
        self._browser_session: Optional[BridgeSessionImpl] = None

    def get_browser_session(self) -> BrowserSession:
        """Get the browser session interface."""
        if self._browser_session is None:
            self._browser_session = BridgeSessionImpl(self.session_id, self.bridge_client)
        return self._browser_session

    async def authenticate_linkedin(self, cookie: str) -> bool:
        """Authenticate with LinkedIn using session cookie."""
        try:
            browser_session = self.get_browser_session()
            
            # Navigate to LinkedIn first
            await browser_session.navigate("https://www.linkedin.com")
            
            # Parse and set the LinkedIn cookie
            if cookie.startswith("li_at="):
                cookie_value = cookie[6:]  # Remove "li_at=" prefix
            else:
                cookie_value = cookie
            
            linkedin_cookie = {
                "name": "li_at",
                "value": cookie_value,
                "domain": ".linkedin.com",
                "path": "/",
                "secure": True,
                "httpOnly": True
            }
            
            await browser_session.set_cookies([linkedin_cookie])
            
            # Navigate to LinkedIn feed to verify authentication
            await browser_session.navigate("https://www.linkedin.com/feed/")
            
            # Wait a moment for navigation
            await asyncio.sleep(2)
            
            # Check if we're authenticated by examining the current URL
            current_url = await browser_session.get_current_url()
            
            if "login" in current_url or "uas/login" in current_url:
                logger.warning("LinkedIn authentication failed - redirected to login page")
                self.authenticated = False
                return False
            
            logger.info("LinkedIn authentication successful via bridge")
            self.authenticated = True
            return True
            
        except Exception as e:
            logger.error(f"LinkedIn authentication failed: {e}")
            self.authenticated = False
            return False

    async def close(self) -> None:
        """Close the bridge session."""
        if self._browser_session:
            await self._browser_session.close()
        
        try:
            await self.bridge_client.close_session(self.session_id)
        except Exception as e:
            logger.warning(f"Error closing bridge session: {e}")


class ChromeBridgeAdapter:
    """Main adapter for Chrome Bridge operations."""
    
    def __init__(self, bridge_url: str = "http://localhost:3000", timeout: int = 30):
        self.bridge_url = bridge_url
        self.timeout = timeout
        self.client = BridgeClient(bridge_url, timeout)
        self._active_sessions: Dict[str, BridgeSession] = {}

    async def is_available(self) -> bool:
        """Check if the bridge server is available."""
        try:
            return await self.client.health_check()
        except Exception as e:
            logger.debug(f"Bridge availability check failed: {e}")
            return False

    async def create_session(self, profile_name: str = "linkedin", headless: bool = True) -> BridgeSession:
        """Create a new Chrome session via bridge."""
        try:
            session_id = await self.client.create_session(profile_name, headless)
            
            bridge_session = BridgeSession(session_id, self.client)
            self._active_sessions[session_id] = bridge_session
            
            logger.info(f"Created bridge session {session_id} for profile {profile_name}")
            return bridge_session
            
        except (BridgeConnectionError, BridgeSessionError) as e:
            logger.error(f"Failed to create bridge session: {e}")
            raise

    async def get_or_create_session(self, profile_name: str = "linkedin", authentication: Optional[str] = None) -> BridgeSession:
        """Get existing session or create a new one with authentication."""
        # For simplicity, we'll create a new session each time
        # In a production implementation, you might want to reuse sessions
        
        try:
            session = await self.create_session(profile_name, headless=True)
            
            # Authenticate if cookie is provided
            if authentication:
                success = await session.authenticate_linkedin(authentication)
                if not success:
                    await session.close()
                    raise BridgeSessionError("LinkedIn authentication failed")
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to get or create authenticated session: {e}")
            raise

    async def list_sessions(self) -> list:
        """List all active sessions."""
        try:
            return await self.client.list_sessions()
        except Exception as e:
            logger.error(f"Failed to list bridge sessions: {e}")
            return []

    async def close_session(self, session_id: str) -> None:
        """Close a specific session."""
        if session_id in self._active_sessions:
            session = self._active_sessions[session_id]
            await session.close()
            del self._active_sessions[session_id]
        else:
            # Try to close via client anyway
            try:
                await self.client.close_session(session_id)
            except Exception as e:
                logger.warning(f"Error closing unknown session {session_id}: {e}")

    async def close_all_sessions(self) -> None:
        """Close all active sessions."""
        for session_id in list(self._active_sessions.keys()):
            await self.close_session(session_id)

    async def close(self) -> None:
        """Close the adapter and all sessions."""
        await self.close_all_sessions()
        await self.client.close()