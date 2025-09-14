# src/linkedin_mcp_server/server.py
"""
FastMCP server implementation for LinkedIn integration with tool registration.

Creates and configures the MCP server with comprehensive LinkedIn tool suite including
person profiles, company data, job information, and session management capabilities.
Provides clean shutdown handling and resource cleanup.
"""

import logging
from typing import Any, Dict

from fastmcp import FastMCP

from linkedin_mcp_server.tools.company import register_company_tools
from linkedin_mcp_server.tools.job import register_job_tools
from linkedin_mcp_server.tools.person import register_person_tools

logger = logging.getLogger(__name__)


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server with all LinkedIn tools."""
    mcp = FastMCP("linkedin_scraper")

    # Register all tools
    register_person_tools(mcp)
    register_company_tools(mcp)
    register_job_tools(mcp)

    # Register session management tool
    @mcp.tool()
    async def close_session() -> Dict[str, Any]:
        """Close the current browser session and clean up resources."""
        from linkedin_mcp_server.drivers.manager import close_all_sessions
        from linkedin_mcp_server.drivers.chrome import close_all_drivers

        try:
            # Close bridge sessions and session manager
            await close_all_sessions()
            
            # Also close any remaining direct Chrome drivers for backward compatibility
            close_all_drivers()
            
            return {
                "status": "success",
                "message": "Successfully closed the browser session and cleaned up resources",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error closing browser session: {str(e)}",
            }

    return mcp


def shutdown_handler() -> None:
    """Clean up resources on shutdown."""
    import asyncio
    from linkedin_mcp_server.drivers.manager import close_all_sessions
    from linkedin_mcp_server.drivers.chrome import close_all_drivers

    # Close bridge sessions and session manager
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, schedule the cleanup
            loop.create_task(close_all_sessions())
        else:
            # If no loop is running, run the cleanup synchronously
            asyncio.run(close_all_sessions())
    except Exception as e:
        logger.warning(f"Error closing bridge sessions during shutdown: {e}")

    # Also close any remaining direct Chrome drivers for backward compatibility
    close_all_drivers()
