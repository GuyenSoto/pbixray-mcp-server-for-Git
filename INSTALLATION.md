# Installing the PBIXRay MCP Server

This document provides instructions for installing and configuring the PBIXRay MCP server with various MCP clients.

## Prerequisites

Before installing the PBIXRay MCP server, make sure you have the following prerequisites:

1. Python 3.8 or higher
2. pip (Python package installer)
3. Any MCP-compatible client

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/username/pbixray-mcp.git
cd pbixray-mcp
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install the core requirements manually:

```bash
pip install mcp pbixray numpy
```

## Configuring with MCP Clients

The PBIXRay MCP server can be used with any MCP-compatible client. Below are instructions for some common clients:

### Generic MCP Client Configuration

In most MCP clients, you'll need to specify the command to start the PBIXRay server. This is typically done in a configuration file with the absolute path to the server script:

```json
{
  "mcpServers": {
    "pbixray": {
      "command": "python",
      "args": ["/path/to/src/pbixray_server.py"]
    }
  }
}
```

Replace `/path/to/src/pbixray_server.py` with the absolute path to the `pbixray_server.py` file on your system.

### Claude Desktop

For Claude Desktop, create or edit the configuration file:

**macOS**:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

Add the following configuration:

```json
{
  "mcpServers": {
    "pbixray": {
      "command": "python",
      "args": ["/path/to/src/pbixray_server.py"]
    }
  }
}
```

### Other MCP-Compatible Clients

For other MCP-compatible clients, refer to their documentation for how to add custom MCP servers. In general, you'll need to provide:

1. A unique name for the server (e.g., "pbixray")
2. The command to run the server (typically "python")
3. Arguments to the command (the path to the server script)

## Running the Server Directly

If you prefer to run the server manually, you can execute it directly:

```bash
python src/pbixray_server.py
```

This will start the server using the stdio transport, which can be useful for testing or for integrating with clients that connect to running servers.

## Troubleshooting

If you encounter issues with the PBIXRay MCP server, try the following steps:

1. **Check your Python version**: Make sure you're using Python 3.8 or higher with `python --version`.

2. **Verify dependencies**: Ensure all required packages are installed with `pip list | grep -E "mcp|pbixray|numpy"`.

3. **Check file paths**: Make sure all paths in your configuration are absolute and correct.

4. **Check file permissions**: Ensure the server script has execute permissions with `chmod +x /path/to/src/pbixray_server.py`.

5. **Test with the demo script**: Run the included demo script to verify the server works correctly:
   ```bash
   python examples/demo.py
   ```

6. **Check logs**: Look for error messages in the console or client logs.

## Using MCP Inspector

The MCP Inspector is a great tool for testing and debugging MCP servers. To use it with the PBIXRay server:

```bash
mcp dev src/pbixray_server.py
```

This will start an interactive session where you can call tools and test responses.

## Getting Help

If you continue to experience issues, check the following resources:

1. [Open an issue](https://github.com/username/pbixray-mcp/issues) on GitHub
2. Check the [Model Context Protocol documentation](https://modelcontextprotocol.io/)
3. Review the [PBIXRay documentation](https://github.com/Hugoberry/pbixray) for underlying functionality