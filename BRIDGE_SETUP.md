# Chrome Bridge Setup Guide

This guide explains how to use the LinkedIn MCP server with Chrome Bridge for seamless Chrome session reuse.

## What is Chrome Bridge?

Chrome Bridge enables the LinkedIn MCP server to reuse your existing Chrome browser session, eliminating the need to:
- Manually paste LinkedIn cookies
- Launch separate Playwright/Chromium instances
- Maintain duplicate login sessions

## Benefits

- **Zero-config authentication** - Uses your existing LinkedIn session
- **Faster startup** - No Chrome driver downloads or initialization
- **Resource efficiency** - Shared browser instances across tools
- **Session persistence** - Maintains login state across operations

## Setup Instructions

### 1. Install mcp-chrome-bridge

First, install the Chrome Bridge server:

```bash
npm install -g mcp-chrome-bridge
```

### 2. Start the Bridge Server

Start the bridge server (keep this running):

```bash
mcp-chrome-bridge
```

By default, it runs on `http://localhost:3000`.

### 3. Configure LinkedIn MCP Server

#### Environment Variables

```bash
export BRIDGE_ENABLED=true
export BRIDGE_URL=http://localhost:3000
export BRIDGE_PROFILE_NAME=linkedin
```

#### CLI Arguments

```bash
# Enable bridge mode
linkedin-mcp-server --bridge

# With custom bridge URL
linkedin-mcp-server --bridge --bridge-url http://localhost:3001

# With custom profile name
linkedin-mcp-server --bridge --bridge-profile my-linkedin-profile

# Disable fallback to Selenium
linkedin-mcp-server --bridge --no-bridge-fallback
```

#### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "linkedin": {
      "command": "linkedin-mcp-server",
      "args": ["--bridge"],
      "env": {
        "BRIDGE_ENABLED": "true",
        "BRIDGE_URL": "http://localhost:3000"
      }
    }
  }
}
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BRIDGE_ENABLED` | `false` | Enable Chrome Bridge mode |
| `BRIDGE_URL` | `http://localhost:3000` | Bridge server URL |
| `BRIDGE_TIMEOUT` | `30` | Connection timeout in seconds |
| `BRIDGE_PROFILE_NAME` | `linkedin` | Chrome profile name |
| `BRIDGE_FALLBACK` | `true` | Enable fallback to Selenium when bridge unavailable |

### CLI Arguments

| Argument | Description |
|----------|-------------|
| `--bridge` | Enable Chrome Bridge mode |
| `--bridge-url URL` | Bridge server URL |
| `--bridge-timeout SECONDS` | Connection timeout |
| `--bridge-profile NAME` | Chrome profile name |
| `--no-bridge-fallback` | Disable Selenium fallback |

## How It Works

1. **Auto-Detection**: The server automatically detects if bridge mode is enabled
2. **Bridge Connection**: Connects to the running bridge server
3. **Session Reuse**: Uses your existing Chrome profile and LinkedIn session
4. **Fallback**: If bridge is unavailable, falls back to Selenium WebDriver (unless disabled)

## Troubleshooting

### Bridge Server Not Found

```
ERROR: Chrome Bridge server is not available
```

**Solution**: Make sure the bridge server is running:
```bash
mcp-chrome-bridge
```

### Connection Timeout

```
ERROR: Failed to connect to bridge at http://localhost:3000
```

**Solutions**:
- Check if the bridge server is running
- Verify the bridge URL is correct
- Check firewall settings

### Bridge Authentication Failed

```
ERROR: LinkedIn authentication failed
```

**Solutions**:
- Make sure you're logged into LinkedIn in your browser
- Clear browser cookies and re-login to LinkedIn
- Check that the profile name matches your Chrome profile

### No Fallback Available

```
ERROR: Bridge unavailable and fallback disabled
```

**Solution**: Either:
- Fix the bridge connection, or
- Remove `--no-bridge-fallback` to enable Selenium fallback

## Advanced Usage

### Custom Chrome Profile

Create a dedicated Chrome profile for LinkedIn MCP:

```bash
# Start Chrome with custom profile
google-chrome --user-data-dir=/path/to/linkedin-profile

# Configure bridge to use this profile
linkedin-mcp-server --bridge --bridge-profile custom-linkedin
```

### Multiple Bridge Instances

Run multiple bridge servers on different ports:

```bash
# Bridge server 1
mcp-chrome-bridge --port 3000

# Bridge server 2
mcp-chrome-bridge --port 3001

# Configure LinkedIn MCP for specific bridge
linkedin-mcp-server --bridge --bridge-url http://localhost:3001
```

### Production Deployment

For production use:

```bash
# Start bridge server with PM2
pm2 start mcp-chrome-bridge --name chrome-bridge

# LinkedIn MCP with production settings
linkedin-mcp-server --bridge --bridge-timeout 60 --no-bridge-fallback
```

## Comparison: Bridge vs Direct WebDriver

| Feature | Chrome Bridge | Direct WebDriver |
|---------|---------------|------------------|
| Setup Complexity | Medium | Low |
| Authentication | Automatic | Manual cookie |
| Resource Usage | Low | High |
| Session Persistence | High | Medium |
| Startup Speed | Fast | Slow |
| Browser Visibility | Uses existing | Hidden/visible |
| Multi-tool Support | Excellent | Good |
| Fallback Options | WebDriver | None |

## Security Considerations

- Bridge communication happens on localhost only
- No credentials are transmitted to the bridge
- Uses existing browser security model
- Session isolation per Chrome profile
- Automatic cleanup on shutdown

## Supported Features

When using bridge mode, the following features are supported:

✅ **Fully Supported**:
- Person profile scraping
- Company profile scraping  
- Job details extraction
- Session management
- Error handling
- Fallback to WebDriver

⚠️ **Limited Support**:
- Some advanced profile fields (interests, accomplishments)
- Job search functionality
- Recommended jobs

The bridge implementation uses JavaScript-based extraction for maximum compatibility and speed.